# <ai_context>
# This file implements a stateful graph for the Polymarket AI agent using LangGraph.
# It orchestrates the following steps:
# 1) Fetch/refresh market data
# 2) Conduct external research with a dedicated "research_agent" node
# 3) Reflect on whether more research is needed or we can proceed
# 4) Conduct market analysis (get market details, orderbook analysis)
# 5) Reflect on whether we need more analysis or can proceed
# 6) Possibly finalize a trade
# 7) Reflect on trade decision or loop back
# 8) End
# </ai_context>

import json
from typing import Any, Dict, List, Literal, Optional, cast

from langchain.schema import AIMessage, BaseMessage, SystemMessage, HumanMessage
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import MemorySaver


from polytrader.configuration import Configuration
from polytrader.gamma import GammaMarketClient
from polytrader.polymarket import Polymarket
from polytrader.state import InputState, OutputState, State
from polytrader.tools import (
    analysis_get_external_news,
    analysis_get_market_trades,
    search_exa,
    search_tavily,
    trade,
    analysis_get_market_details,
    analysis_get_multi_level_orderbook,
    analysis_get_historical_trends,
)
from polytrader.utils import init_model

###############################################################################
# Global references
###############################################################################
gamma_client = GammaMarketClient()
poly_client = Polymarket()

###############################################################################
# Node: Fetch Market Data
###############################################################################
async def fetch_market_data(state: State) -> Dict[str, Any]:
    """
    Fetch or refresh data from Gamma about the specified market_id.
    Store raw JSON in state.market_data for downstream usage.
    """
    state.loop_step += 1
    market_id = state.market_id

    if market_id is None:
        return {
            "messages": ["No market_id provided; skipping market data fetch."],
            "proceed": False,
        }

    try:
        # Convert market_id to int for API call, but keep original string version
        market_id_int = int(market_id)
        market_json = gamma_client.get_market(market_id_int)
        
        # Convert any large integers in the response to strings
        if "id" in market_json:
            market_json["id"] = str(market_json["id"])
        if "clobTokenIds" in market_json:
            market_json["clobTokenIds"] = [str(tid) for tid in json.loads(market_json["clobTokenIds"])]
            
        state.market_data = market_json  # raw dict
        print("Raw market data as json:")
        print(json.dumps(market_json, indent=2))
        return {
            "messages": [f"Fetched market data for ID={market_id}."],
            "proceed": True,
            "market_data": market_json,
        }
    except ValueError as e:
        return {
            "messages": [f"Invalid market ID format: {market_id}"],
            "proceed": False,
        }
    except Exception as e:
        return {
            "messages": [f"Error fetching market data: {str(e)}"],
            "proceed": False,
        }

###### RESEARCH ####### 

###############################################################################
# Node: Research Agent
###############################################################################
async def research_agent_node(
    state: State, *, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    """
    Sub-agent dedicated to external research only.
    This node generates the research strategy and interprets results.
    """
    # Load configuration
    configuration = Configuration.from_runnable_config(config)

    # Define the 'Info' tool, which is the user-defined extraction schema
    external_research_info_tool = {
        "name": "ExternalResearchInfo",
        "description": "Call this when you have gathered sufficient research from the web on the market's subject. This will be used to update the info you have about the topic.",
        "parameters": {
            "type": "object",
            "properties": {
                "research_summary": {
                    "type": "string",
                    "description": "A comprehensive summary of the research findings"
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence level in the research findings (0-1)"
                },
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of sources used in research"
                }
            },
            "required": ["research_summary", "confidence", "sources"]
        }
    }

    # Format the prompt
    p = configuration.research_agent_prompt.format(
        info=json.dumps(state.extraction_schema, indent=2), 
        market_data=json.dumps(state.market_data or {}, indent=2), 
        question=state.market_data["question"], 
        description=state.market_data["description"], 
        outcomes=state.market_data["outcomes"]
    )

    # Combine with conversation so far
    messages = [HumanMessage(content=p)] + state.messages

    # Create the model and bind tools
    raw_model = init_model(config)
    model = raw_model.bind_tools([
        search_exa,
        # search_tavily,
        external_research_info_tool
    ], tool_choice="any")

    # Call the model
    response = cast(AIMessage, await model.ainvoke(messages))

    # Initialize info to None
    info = None

    print("RESPONSE:")
    print(response)

    # Check if the response has tool calls
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "ExternalResearchInfo":
                info = tool_call["args"]
                break
    if info is not None:
        response.tool_calls = [
            tc for tc in response.tool_calls if tc["name"] == "ExternalResearchInfo"
        ]
    response_messages: List[BaseMessage] = [response]
    if not response.tool_calls:  # If LLM didn't call any tool
        response_messages.append(
            HumanMessage(content="Please respond by calling one of the provided tools.")
        )

    return {
        "messages": response_messages,
        "external_research_info": info,
        "loop_step": state.loop_step + 1,
    }

class InfoIsSatisfactory(BaseModel):
    """Validate whether the current extracted info is satisfactory and complete."""

    reason: List[str] = Field(
        description="First, provide reasoning for why this is either good or bad as a final result. Must include at least 3 reasons."
    )
    is_satisfactory: bool = Field(
        description="After providing your reasoning, provide a value indicating whether the result is satisfactory. If not, you will continue researching."
    )
    improvement_instructions: Optional[str] = Field(
        description="If the result is not satisfactory, provide clear and specific instructions on what needs to be improved or added to make the information satisfactory."
        " This should include details on missing information, areas that need more depth, or specific aspects to focus on in further research.",
        default=None,
    )

###############################################################################
# Node: Reflect on Research
###############################################################################
async def reflect_on_research_node(
    state: State, *, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    """
    This node checks if the research information gathered is satisfactory.
    It uses a structured output model to evaluate the quality of research.
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"{reflect_on_research_node.__name__} expects the last message in the state to be an AI message with tool calls."
            f" Got: {type(last_message)}"
        )

    # Build the system message
    market_data_str = json.dumps(state.market_data or {}, indent=2)
    system_text = """You are evaluating the quality of web research gathered about a market.
Your role is to determine if the research is sufficient to proceed with market analysis.
"""
    system_msg = SystemMessage(content=f"{system_text}\n\nMarket data:\n{market_data_str}")

    # Create messages list
    messages = [system_msg] + state.messages[:-1]
    
    # Get the presumed info
    presumed_info = state.external_research_info
    checker_prompt = """I am evaluating the research information below. 
Is this sufficient to proceed with market analysis? Give your reasoning.
Consider factors like comprehensiveness, relevance, and reliability of sources.
If you don't think it's sufficient, be specific about what needs to be improved.

Research Information:
{presumed_info}"""
    
    p1 = checker_prompt.format(presumed_info=json.dumps(presumed_info or {}, indent=2))
    messages.append(HumanMessage(content=p1))

    # Initialize and configure the model
    raw_model = init_model(config)
    bound_model = raw_model.with_structured_output(InfoIsSatisfactory)
    response = cast(InfoIsSatisfactory, await bound_model.ainvoke(messages))

    if response.is_satisfactory and presumed_info:
        return {
            "external_research_info": presumed_info,
            "messages": [
                ToolMessage(
                    tool_call_id=last_message.tool_calls[0]["id"],
                    content="\n".join(response.reason),
                    name="ExternalResearchInfo",
                    additional_kwargs={"artifact": response.model_dump()},
                    status="success",
                )
            ],
            "decision": "proceed_to_analysis"
        }
    else:
        return {
            "messages": [
                ToolMessage(
                    tool_call_id=last_message.tool_calls[0]["id"],
                    content=f"Research needs improvement:\n{response.improvement_instructions}",
                    name="ExternalResearchInfo",
                    additional_kwargs={"artifact": response.model_dump()},
                    status="error",
                )
            ],
            "decision": "research_more"
        }

###### ANALYSIS #######

###############################################################################
# Node: Analysis Agent
###############################################################################
async def analysis_agent_node(
    state: State, *, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    """
    Sub-agent that focuses on numeric Polymarket analysis.
    This node interprets numeric data, orderbook, and trends from Polymarket.
    """
    configuration = Configuration.from_runnable_config(config)

    # Define the 'AnalysisInfo' tool with enhanced schema
    analysis_info_tool = {
        "name": "AnalysisInfo",
        "description": "Call this when you have completed your analysis. Provide a comprehensive analysis of all market data gathered from the tools.",
        "parameters": {
            "type": "object",
            "properties": {
                "analysis_summary": {
                    "type": "string",
                    "description": "A comprehensive summary of all market analysis findings"
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence level in the analysis (0-1)"
                },
                "market_metrics": {
                    "type": "object",
                    "description": "Analysis of key market metrics",
                    "properties": {
                        "price_analysis": {
                            "type": "string",
                            "description": "Analysis of current prices, spreads, and price movements"
                        },
                        "volume_analysis": {
                            "type": "string",
                            "description": "Analysis of trading volumes and activity"
                        },
                        "liquidity_analysis": {
                            "type": "string",
                            "description": "Analysis of market liquidity and depth"
                        }
                    }
                },
                "orderbook_analysis": {
                    "type": "object",
                    "description": "Analysis of order book data",
                    "properties": {
                        "market_depth": {
                            "type": "string",
                            "description": "Analysis of bid/ask depth and imbalances"
                        },
                        "execution_analysis": {
                            "type": "string",
                            "description": "Analysis of potential execution prices and slippage"
                        },
                        "liquidity_distribution": {
                            "type": "string",
                            "description": "Analysis of how liquidity is distributed in the book"
                        }
                    }
                },
                "trading_signals": {
                    "type": "object",
                    "description": "Key trading signals and indicators",
                    "properties": {
                        "price_momentum": {
                            "type": "string",
                            "description": "Analysis of price momentum and trends"
                        },
                        "market_efficiency": {
                            "type": "string",
                            "description": "Analysis of market efficiency and potential opportunities"
                        },
                        "risk_factors": {
                            "type": "string",
                            "description": "Identified risk factors and concerns"
                        }
                    }
                },
                "execution_recommendation": {
                    "type": "object",
                    "description": "Recommendations for trade execution",
                    "properties": {
                        "optimal_size": {
                            "type": "string",
                            "description": "Recommended trade size based on market depth"
                        },
                        "entry_strategy": {
                            "type": "string",
                            "description": "Recommended approach for trade entry"
                        },
                        "key_levels": {
                            "type": "string",
                            "description": "Important price levels to watch"
                        }
                    }
                }
            },
            "required": [
                "analysis_summary",
                "confidence",
                "market_metrics",
                "orderbook_analysis",
                "trading_signals",
                "execution_recommendation"
            ]
        }
    }

    # Format the prompt with required data checks
    required_data_checks = {
        "market_details": state.market_details is not None,
        "orderbook_data": state.orderbook_data is not None,
        "historical_trends": state.historical_trends is not None
    }

    # Build the prompt with data availability info
    p = configuration.analysis_agent_prompt.format(
        info=json.dumps(analysis_info_tool["parameters"], indent=2),
        market_data=json.dumps(state.market_data or {}, indent=2),
        question=state.market_data["question"] if state.market_data else "",
        description=state.market_data["description"] if state.market_data else "",
        outcomes=state.market_data["outcomes"] if state.market_data else ""
    )

    # Add data availability check to prompt
    data_check_prompt = "\nData Availability Status:\n"
    for data_type, is_available in required_data_checks.items():
        if not is_available:
            data_check_prompt += f"- {data_type}: NOT AVAILABLE - Please use appropriate tool to fetch this data\n"
        else:
            data_check_prompt += f"- {data_type}: Available\n"
    
    p += data_check_prompt

    # Combine with conversation so far
    messages = [HumanMessage(content=p)] + state.messages

    # Create the model and bind tools
    raw_model = init_model(config)
    model = raw_model.bind_tools([
        analysis_get_market_details,
        analysis_get_multi_level_orderbook,
        analysis_get_historical_trends,
        analysis_get_external_news,
        analysis_get_market_trades,
        analysis_info_tool
    ], tool_choice="any")

    # Call the model
    response = cast(AIMessage, await model.ainvoke(messages))
    info = None

    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "AnalysisInfo":
                info = tool_call["args"]
                break
        if info is not None:
            # Keep only the AnalysisInfo tool call in the final response
            response.tool_calls = [
                tc for tc in response.tool_calls if tc["name"] == "AnalysisInfo"
            ]
            # Store the complete analysis info in state
            state.analysis_info = info

    response_messages: List[BaseMessage] = [response]
    if not response.tool_calls:  # If LLM didn't call any tool
        response_messages.append(
            HumanMessage(content="Please respond by calling one of the provided tools to gather data before finalizing your analysis.")
        )

    return {
        "messages": response_messages,
        "analysis_info": info,
        "proceed": True,
        "loop_step": state.loop_step + 1,
    }

class AnalysisIsSatisfactory(BaseModel):
    """Validate whether the market analysis is satisfactory and complete."""

    reason: List[str] = Field(
        description="First, provide reasoning for why this analysis is either good or bad as a final result. Must include at least 3 reasons."
    )
    is_satisfactory: bool = Field(
        description="After providing your reasoning, provide a value indicating whether the analysis is satisfactory. If not, you will continue analyzing."
    )
    improvement_instructions: Optional[str] = Field(
        description="If the analysis is not satisfactory, provide clear and specific instructions on what needs to be improved or added to make the analysis satisfactory.",
        default=None,
    )

###############################################################################
# Node: Reflect on Analysis
###############################################################################
async def reflect_on_analysis_node(
    state: State, *, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    """
    This node checks if the market analysis is satisfactory.
    It uses a structured output model to evaluate the quality of analysis.
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"{reflect_on_analysis_node.__name__} expects the last message in the state to be an AI message."
            f" Got: {type(last_message)}"
        )

    market_data_str = json.dumps(state.market_data or {}, indent=2)
    system_text = """You are evaluating the quality of market analysis based on available Polymarket data.
Your role is to determine if we have sufficient information to make an informed trading decision.

Available Data Sources:
1. Market Details: Current prices, volumes, spreads, and basic market metrics
2. Orderbook Data: Current order book state with bid/ask levels
3. Market Trades: Recent trade activity and prices
4. Basic Historical Data: Limited historical price and volume information

Focus on evaluating whether we have:
1. Clear understanding of current market prices and spreads
2. Sufficient liquidity assessment for intended trading
3. Basic market sentiment from recent trading activity
4. Reasonable risk assessment based on available metrics

Do NOT require:
- Detailed time-series analysis (not available from API)
- Historical liquidity profiles (not available)
- Complex volatility calculations
- Order flow imbalance analysis
"""
    system_msg = SystemMessage(content=f"{system_text}\n\nMarket data:\n{market_data_str}")

    messages = [system_msg] + state.messages[:-1]
    
    analysis_info = state.analysis_info
    checker_prompt = """I am evaluating if we have sufficient market analysis to make a trading decision.

Key Questions:
1. Do we understand the current market price levels and spreads?
2. Do we have a clear picture of available liquidity for trading?
3. Can we assess basic market sentiment from recent activity?
4. Do we have enough information to identify major trading risks?

Remember: We are limited to current market data and basic historical information from Polymarket's APIs.
Focus on whether the analysis makes good use of the available data rather than requesting unavailable metrics.

Analysis Information:
{analysis_info}"""
    
    p1 = checker_prompt.format(analysis_info=json.dumps(analysis_info or {}, indent=2))
    messages.append(HumanMessage(content=p1))

    raw_model = init_model(config)
    bound_model = raw_model.with_structured_output(AnalysisIsSatisfactory)
    response = cast(AnalysisIsSatisfactory, await bound_model.ainvoke(messages))

    if response.is_satisfactory and analysis_info:
        return {
            "analysis_info": analysis_info,
            "messages": [
                ToolMessage(
                    tool_call_id=last_message.tool_calls[0]["id"] if last_message.tool_calls else "",
                    content="\n".join(response.reason),
                    name="Analysis",
                    additional_kwargs={"artifact": response.model_dump()},
                    status="success",
                )
            ],
            "decision": "proceed_to_trade"
        }
    else:
        return {
            "messages": [
                ToolMessage(
                    tool_call_id=last_message.tool_calls[0]["id"] if last_message.tool_calls else "",
                    content=f"Analysis needs improvement:\n{response.improvement_instructions}",
                    name="Analysis",
                    additional_kwargs={"artifact": response.model_dump()},
                    status="error",
                )
            ],
            "decision": "analysis_more"
        }

###### TRADE #######

class TradeIsSatisfactory(BaseModel):
    """Validate whether the trade decision is satisfactory and complete."""

    reason: List[str] = Field(
        description="First, provide reasoning for why this trade decision is either good or bad as a final result. Must include at least 3 reasons."
    )
    is_satisfactory: bool = Field(
        description="After providing your reasoning, provide a value indicating whether the trade decision is satisfactory. If not, you will continue refining."
    )
    improvement_instructions: Optional[str] = Field(
        description="If the trade decision is not satisfactory, provide clear and specific instructions on what needs to be improved or reconsidered.",
        default=None,
    )

###############################################################################
# Node: Trade Agent
###############################################################################
async def trade_agent_node(
    state: State, *, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    """
    Sub-agent for finalizing trade decisions.
    This node makes the final trade decision based on research and analysis.
    """

    configuration = Configuration.from_runnable_config(config)

    ###########################################################################
    # Evaluate whether user has positions
    ###########################################################################
    position_info = state.positions or {}
    # Check if user has any position for the relevant market or token
    # The LLM does not necessarily know the token ID yet, so we keep it flexible
    # We'll just instruct the LLM about what is possible in general:
    user_has_positions = any(position_info.values())  # True if any positive size

    # The user can do NO_TRADE or BUY in all scenarios
    # The user can SELL only if they have an existing position
    # We'll pass a short explanation in the system prompt
    possible_sides = ["BUY", "NO_TRADE"]
    if user_has_positions:
        possible_sides = ["BUY", "SELL", "NO_TRADE"]

    ###########################################################################
    # Define the trade decision tool with updated schema
    ###########################################################################
    trade_decision_tool = {
        "name": "TradeDecision",
        "description": (
            "Call this when you have made your final trade decision. "
            f"You may only set 'side' to one of {possible_sides}. "
            "This will record your decision and reasoning."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "side": {
                    "type": "string",
                    "description": f"Your trading side. Must be one of: {possible_sides}",
                    "enum": possible_sides
                },
                "market_id": {
                    "type": "string",
                    "description": "The market ID for which the trade is being made (as a string)."
                },
                "token_id": {
                    "type": "string",
                    "description": "The token ID that the user should trade or hold (as a string)."
                },
                "size": {
                    "type": "number",
                    "description": (
                        "The size (in USDC or shares) that the user should trade. "
                        "If side=NO_TRADE, typically set this to 0. "
                        "Must not exceed 'available_funds' if side=BUY."
                    )
                },
                "reason": {
                    "type": "string",
                    "description": "Clear and detailed reasoning for the trade decision."
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence level in the decision (0-1).",
                    "minimum": 0,
                    "maximum": 1
                },
                "trade_evaluation_of_market_data": {
                    "type": "string",
                    "description": "Evaluation of market data that led to this decision."
                }
            },
            "required": [
                "side",
                "market_id",
                "token_id",
                "size",
                "reason",
                "confidence"
            ]
        }
    }

    # Build a comprehensive prompt that includes all available information
    system_text = f"""You are a trade decision maker. Your task is to make a SINGLE, CLEAR trade decision based on all available information.
You must use the TradeDecision tool ONCE to record your decision. Do not make multiple trade calls.

Available Information:
1. Market Data: {json.dumps(state.market_data or {}, indent=2)}
2. Research Info: {json.dumps(state.external_research_info or {}, indent=2)}
3. Analysis Info: {json.dumps(state.analysis_info or {}, indent=2)}
4. User Positions (for this or related markets): {json.dumps(state.positions or {}, indent=2)}
5. User's Available Funds for a new position: {state.available_funds}

You MAY ONLY choose 'side' from this list: {possible_sides}.

If the user does not hold any position in this market, you may NOT choose SELL. 
You can either buy or do no trade.

If the user already has a position, you can consider SELL as well.

Be sure to respect the user's 'available_funds' if you recommend buying. 
Do not propose a trade that exceeds these available funds.

When you have finalized your decision, call the TradeDecision tool exactly once.
"""

    messages = [HumanMessage(content=system_text)] + state.messages

    raw_model = init_model(config)
    model = raw_model.bind_tools([trade, trade_decision_tool], tool_choice="any")

    response = await model.ainvoke(messages)
    if not isinstance(response, AIMessage):
        response = AIMessage(content=str(response))

    trade_info = None
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "TradeDecision":
                trade_info = tool_call["args"]
                break
        if trade_info is not None:
            response.tool_calls = [tc for tc in response.tool_calls if tc["name"] == "TradeDecision"]
            # Store the trade info in state
            state.trade_info = trade_info
            state.trade_decision = trade_info.get("side")
            state.confidence = float(trade_info.get("confidence", 0))

    new_messages: List[BaseMessage] = [response]
    if not response.tool_calls:
        new_messages.append(
            HumanMessage(content="Please make your final trade decision by calling the TradeDecision tool ONCE.")
        )

    return {
        "messages": new_messages,
        "trade_info": trade_info,
        "proceed": True,
        "loop_step": state.loop_step + 1,
    }

###############################################################################
# Node: Reflect on Trade
###############################################################################
async def reflect_on_trade_node(
    state: State, *, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    """
    This node validates that the trade decision is complete and properly formatted.
    If valid, the workflow will end. If invalid, it will request a new trade decision.
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"{reflect_on_trade_node.__name__} expects the last message in the state to be an AI message."
            f" Got: {type(last_message)}"
        )

    # Define validation criteria
    required_fields = {
        "side": lambda x: x in ["BUY", "SELL", "NO_TRADE"],
        "reason": lambda x: isinstance(x, str) and len(x) > 0,
        "confidence": lambda x: isinstance(x, (int, float)) and 0 <= float(x) <= 1,
        "market_id": lambda x: isinstance(x, str),
        "token_id": lambda x: isinstance(x, str),
        "size": lambda x: isinstance(x, (int, float))
    }

    system_text = """You are validating a trade decision. Your task is to ensure the decision is complete and properly formatted.

Required Fields:
- side: Must be one of "BUY", "SELL", "NO_TRADE"
- market_id: Must be a string
- token_id: Must be a string
- size: Must be a number
- reason: Must be a non-empty string with clear reasoning
- confidence: Must be a number between 0 and 1

The decision should be clear, well-reasoned, and based on the available market data and analysis.
If side=NO_TRADE, size can be 0.
If side=BUY, size must not exceed available funds.
If side=SELL, user must have a position in the market (though the LLM check is partial).
"""
    system_msg = SystemMessage(content=system_text)

    messages = [system_msg] + state.messages[:-1]
    
    trade_info = state.trade_info
    checker_prompt = """Evaluate the following trade decision:

{trade_info}

Validation Criteria:
1. All required fields are present and properly formatted
2. The decision is clear and unambiguous
3. The reasoning is well-supported by the available data
4. The confidence level is appropriate given the reasoning
5. If side=NO_TRADE, ensure size=0
6. If side=BUY, ensure size does not exceed available_funds
7. If side=SELL, ensure the user has a position in that token.

Should this trade decision be accepted as final?"""
    
    p1 = checker_prompt.format(trade_info=json.dumps(trade_info or {}, indent=2))
    messages.append(HumanMessage(content=p1))

    raw_model = init_model(config)
    bound_model = raw_model.with_structured_output(TradeIsSatisfactory)
    response = cast(TradeIsSatisfactory, await bound_model.ainvoke(messages))

    # Validate required fields
    is_valid = True
    validation_errors = []
    
    if trade_info:
        for field, validator in required_fields.items():
            value = trade_info.get(field)
            if value is None:
                is_valid = False
                validation_errors.append(f"Missing required field: {field}")
            elif not validator(value):
                is_valid = False
                validation_errors.append(f"Invalid value for {field}: {value}")
        # Additional checks
        side_val = trade_info.get("side", "")
        size_val = trade_info.get("size", 0)
        if side_val == "NO_TRADE" and size_val != 0:
            is_valid = False
            validation_errors.append("If side=NO_TRADE, size must be 0.")
        if side_val == "BUY":
            if size_val is not None and size_val > state.available_funds:
                is_valid = False
                validation_errors.append(f"Cannot BUY with size {size_val} exceeding available funds {state.available_funds}.")
        if side_val == "SELL":
            # check position if the user has the token
            token_val = trade_info.get("token_id", "")
            if not state.positions or state.positions.get(token_val, 0) <= 0:
                is_valid = False
                validation_errors.append(f"Cannot SELL token {token_val} if user holds no position in it.")
    else:
        is_valid = False
        validation_errors.append("No trade decision provided")

    final_is_satisfactory = response.is_satisfactory and is_valid

    if final_is_satisfactory:
        return {
            "trade_info": trade_info,
            "messages": [
                ToolMessage(
                    tool_call_id=last_message.tool_calls[0]["id"] if last_message.tool_calls else "",
                    content="Trade decision validated successfully:\n" + "\n".join(response.reason),
                    name="Trade",
                    additional_kwargs={"artifact": response.model_dump()},
                    status="success",
                )
            ],
            "decision": "end"
        }
    else:
        # Combine pydantic-based improvement instructions with our local validation errors
        combined_errors = "\n".join(validation_errors)
        if response.improvement_instructions:
            combined_errors += f"\nAdditional suggestions: {response.improvement_instructions}"

        return {
            "messages": [
                ToolMessage(
                    tool_call_id=last_message.tool_calls[0]["id"] if last_message.tool_calls else "",
                    content=f"Trade decision needs improvement:\n{combined_errors}",
                    name="Trade",
                    additional_kwargs={"artifact": response.model_dump()},
                    status="error",
                )
            ],
            "decision": "trade_more"
        }

###############################################################################
# Routing
###############################################################################
def route_after_fetch(state: State) -> Literal["research_agent", "__end__"]:
    """After fetch, we always go to the research_agent (unless there's no data)."""
    if not state.market_data:
        return "__end__"
    # Reset loop step when starting research
    state.loop_step = 0
    return "research_agent"

def route_after_research_agent(state: State) -> Literal["research_agent", "research_tools", "reflect_on_research"]:
    """After research agent, check if we need to execute tools or reflect."""
    print("INSIDE ROUTE AFTER RESEARCH AGENT")
    last_msg = state.messages[-1]
    
    if not isinstance(last_msg, AIMessage):
        return "research_agent"
    
    if last_msg.tool_calls and last_msg.tool_calls[0]["name"] == "ExternalResearchInfo":
        return "reflect_on_research"
    else:
        return "research_tools"

def route_after_reflect_on_research(state: State, *, config: Optional[RunnableConfig] = None) -> Literal["research_agent", "analysis_agent", "__end__"]:
    configuration = Configuration.from_runnable_config(config)

    last_msg = state.messages[-1] if state.messages else None
    if not isinstance(last_msg, ToolMessage):
        return "research_agent"
    
    if last_msg.status == "success":
        # Reset loop step when moving to analysis agent
        state.loop_step = 0
        return "analysis_agent"
    elif last_msg.status == "error":
        if state.loop_step >= configuration.max_loops:
            return "__end__"
        return "research_agent"
    
    return "research_agent"

def route_after_analysis(state: State) -> Literal["analysis_agent", "analysis_tools", "reflect_on_analysis"]:
    """After analysis agent, check if we need to execute tools or reflect."""
    last_msg = state.messages[-1] if state.messages else None
    
    if not isinstance(last_msg, AIMessage):
        return "analysis_agent"
    
    if last_msg.tool_calls and last_msg.tool_calls[0]["name"] == "AnalysisInfo":
        return "reflect_on_analysis"
    else: 
        return "analysis_tools"

def route_after_reflect_on_analysis(state: State, *, config: Optional[RunnableConfig] = None) -> Literal["analysis_agent", "trade_agent", "__end__"]:
    configuration = Configuration.from_runnable_config(config)

    last_msg = state.messages[-1] if state.messages else None
    if not isinstance(last_msg, ToolMessage):
        return "analysis_agent"
    
    if last_msg.status == "success":
        # Reset loop step when moving to trade agent
        state.loop_step = 0
        return "trade_agent"
    elif last_msg.status == "error":
        if state.loop_step >= configuration.max_loops:
            return "__end__"
        return "analysis_agent"
    
    return "analysis_agent"

def route_after_trade(state: State) -> Literal["trade_agent", "reflect_on_trade", "trade_tools"]:
    """After trade agent, route to reflection if a trade decision was made."""
    last_msg = state.messages[-1] if state.messages else None
    
    if not isinstance(last_msg, AIMessage):
        return "trade_agent"
    
    # Check if we have a TradeDecision tool call
    if last_msg.tool_calls and any(tc["name"] == "TradeDecision" for tc in last_msg.tool_calls):
        return "reflect_on_trade"
    else:
        return "trade_tools"

def route_after_reflect_on_trade(state: State, *, config: Optional[RunnableConfig] = None) -> Literal["trade_agent", "__end__"]:
    """After reflection, either end the workflow or request a new trade decision."""
    configuration = Configuration.from_runnable_config(config)

    last_msg = state.messages[-1] if state.messages else None
    if not isinstance(last_msg, ToolMessage):
        return "trade_agent"
    
    # If validation was successful, end the workflow
    if last_msg.status == "success":
        return "__end__"
    
    # If we've exceeded max loops, end anyway
    if state.loop_step >= configuration.max_loops:
        return "__end__"
    
    # Otherwise, try one more trade decision
    return "trade_agent"

###############################################################################
# Construct the Graph
###############################################################################
workflow = StateGraph(State, input=InputState, output=OutputState, config_schema=Configuration)


workflow.add_edge("__start__", "fetch_market_data")
workflow.add_node("fetch_market_data", fetch_market_data)
workflow.add_conditional_edges("fetch_market_data", route_after_fetch)

# Research 
workflow.add_node("research_tools", ToolNode([
    search_exa,
    # search_tavily
]))
workflow.add_node("research_agent", research_agent_node)
workflow.add_node("reflect_on_research", reflect_on_research_node)
workflow.add_conditional_edges("research_agent", route_after_research_agent)
workflow.add_edge("research_tools", "research_agent")
workflow.add_conditional_edges("reflect_on_research", route_after_reflect_on_research)

# Analysis
workflow.add_node("analysis_tools", ToolNode([
    analysis_get_market_details,
    analysis_get_multi_level_orderbook,
    analysis_get_historical_trends,
    analysis_get_external_news,
    analysis_get_market_trades
]))
workflow.add_node("analysis_agent", analysis_agent_node)
workflow.add_node("reflect_on_analysis", reflect_on_analysis_node)
workflow.add_conditional_edges("analysis_agent", route_after_analysis)
workflow.add_edge("analysis_tools", "analysis_agent")
workflow.add_conditional_edges("reflect_on_analysis", route_after_reflect_on_analysis)

# Trade
workflow.add_node("trade_tools", ToolNode([
    trade
]))
workflow.add_node("trade_agent", trade_agent_node)
workflow.add_node("reflect_on_trade", reflect_on_trade_node)
workflow.add_edge("trade_tools", "trade_agent")
workflow.add_conditional_edges("trade_agent", route_after_trade)
workflow.add_conditional_edges("reflect_on_trade", route_after_reflect_on_trade)

# Set up memory
memory = MemorySaver()

# Compile
graph = workflow.compile(checkpointer=memory)
graph.name = "PolymarketAgent"