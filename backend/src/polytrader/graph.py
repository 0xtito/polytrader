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
from datetime import datetime

from langchain.schema import AIMessage, BaseMessage, SystemMessage, HumanMessage
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt, Command
from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import MemorySaver


from polytrader.configuration import Configuration
from polytrader.gamma import GammaMarketClient
from polytrader.polymarket import Polymarket
from polytrader.state import InputState, OutputState, ResearchResult, State, Token, TradeDecision
from polytrader.tools import (
    analysis_get_external_news,
    analysis_get_market_trades,
    search_exa,
    search_tavily,
    trade,
    analysis_get_market_details,
    analysis_get_multi_level_orderbook,
    analysis_get_historical_trends,
    deep_research 
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

        if not state.tokens:
            print("SETTING TOKENS")
            # Parse outcomes from JSON string if needed
            outcomes = json.loads(market_json["outcomes"]) if isinstance(market_json["outcomes"], str) else market_json["outcomes"]
            clob_token_ids = market_json["clobTokenIds"]
            
            print("outcomes: ", outcomes)
            print("clobTokenIds: ", clob_token_ids)
            
            # Create Token objects with proper YES/NO outcomes
            tokens: List[Token] = []
            for token_id, outcome in zip(clob_token_ids, outcomes):
                # Normalize outcome to YES/NO format
                normalized_outcome = "YES" if outcome.lower() == "yes" else "NO"
                tokens.append(Token(token_id=token_id, outcome=normalized_outcome))
            
            print("TOKENS: ", tokens)
            state.tokens = tokens
        else: 
            print("TOKENS ALREADY SET")

        state.market_data = market_json  # raw dict
        print("Raw market data as json:")
        return {
            "messages": [f"Fetched market data for ID={market_id}."],
            "proceed": True,
            "market_data": market_json,
            "tokens": tokens
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

    last_message = state.messages[-1]

    research_report = None

    if isinstance(last_message, ToolMessage) and last_message.name == "deep_research":
        print("IS TOOL MESSAGE")
        print(last_message)
        try:
            # Parse the content into a ResearchResult if it's a dictionary
            content = last_message.content
            if isinstance(content, dict):
                print("IS DICT")
                research_report = ResearchResult(**content)
            elif isinstance(content, ResearchResult):
                print("IS RESEARCH RESULT")
                research_report = content
            else:
                print("IS NOT DICT OR RESEARCH RESULT")
                # Try to parse string content as JSON
                try:
                    content_dict = json.loads(content)
                    # Doing this to ensure the content is a ResearchResult
                    research_report = ResearchResult(**content_dict)
                except json.JSONDecodeError:
                    print("Could not parse research report content as JSON")
                    # return {
                    #     "messages": [last_message],
                    #     "research_report": None,
                    #     "loop_step": state.loop_step + 1,
                    # }

            # Update state with the ResearchResult
            if research_report:
                state.research_report = research_report.model_dump()

            last_ai_message = state.messages[-2]

            # Create an AIMessage with the research result as a tool call
            ai_message = AIMessage(
                content="Research completed successfully. Please evaluate the results.",
                tool_calls=[{
                    "id": last_ai_message.tool_calls[0]["id"],
                    "name": last_ai_message.tool_calls[0]["name"],
                    "args": last_ai_message.tool_calls[0]["args"]
                }]
            )


            return {
                "messages": [ai_message],
                "research_report": state.research_report,
                "loop_step": state.loop_step + 1,
            }
        except Exception as e:
            print(f"Error parsing research report: {e}")
            return {
                "messages": [last_message],
                "research_report": None,
                "loop_step": state.loop_step + 1,
            }

    # Format the prompt
    p = configuration.research_agent_prompt.format(
        market_data=json.dumps(state.market_data or {}, indent=2), 
        question=state.market_data.get("question", ""), 
        description=state.market_data.get("description", ""), 
        outcomes=state.market_data.get("outcomes", [])
    )

    # Combine with conversation so far
    messages = [HumanMessage(content=p)] + state.messages

    # Create the model and bind tools
    raw_model = init_model(config)
    model = raw_model.bind_tools([deep_research], tool_choice="any")

    # Call the model
    response = cast(AIMessage, await model.ainvoke(messages))

    # Return response with updated state
    return {
        "messages": [response],
        "research_report": state.research_report,
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
    system_text = f"""You are evaluating the quality of web research gathered about a market.
Your role is to determine if the research is sufficient to proceed with market analysis.

The research report is meant to help answer the question: <question>{state.market_data.get("question", "")}</question>.
"""
    system_msg = SystemMessage(content=system_text)

    # Create messages list
    messages = [system_msg] + state.messages[:-1]
    
    # Get the research result
    research_result = state.research_report
    checker_prompt = """I am evaluating the research information below. 
Is this sufficient to proceed with market analysis? Give your reasoning.
Consider factors like comprehensiveness, relevance, and reliability of sources. 
If you don't think it's sufficient, be specific about what needs to be improved.

When evaluating this research report, focus on how well it answers the core question: <question>{question}</question>. The priority is gathering relevant factual information and qualitative insights - do not worry about numerical analysis or quantitative metrics at this stage.

Research Information:
Report: {report}

Key Learnings:
{learnings}

Sources:
{sources}"""
    
    p1 = checker_prompt.format(
        question=state.market_data.get("question", "") if research_result else "",
        report=research_result.get("report", "") if research_result else "",
        learnings="\n".join([f"- {learning}" for learning in research_result.get("learnings", [])]) if research_result else "",
        sources="\n".join([f"- {url}" for url in research_result.get("visited_urls", [])]) if research_result else ""
    )

    print("P1: ", p1)
    messages.append(HumanMessage(content=p1))

    # Initialize and configure the model
    raw_model = init_model(config)
    bound_model = raw_model.with_structured_output(InfoIsSatisfactory)
    response = cast(InfoIsSatisfactory, await bound_model.ainvoke(messages))

    print("REFLECT ON RESEARCH RESPONSE: ", response)

    if response.is_satisfactory:
        return {
            "research_report": research_result,
            "messages": [
                ToolMessage(
                    tool_call_id=last_message.tool_calls[0]["id"],
                    content="\n".join(response.reason),
                    name="deep_research",
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
                    name="deep_research",
                    additional_kwargs={
                        "artifact": response.model_dump(),
                        "improvement_instructions": response.improvement_instructions
                    },
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
        "description": "Call this when you have completed your quantitative analysis. Provide a comprehensive quantitative analysis of all market data gathered from the tools.",
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

    # Build the system text with comprehensive instructions
    system_text = """You are a market analysis expert focused on analyzing Polymarket prediction markets.
Your task is to perform a comprehensive market analysis using all available data sources and tools.

Available Analysis Tools:
1. Market Details (analysis_get_market_details):
   - Current prices, volumes, spreads
   - Basic market metrics and parameters
   - Outcome prices and options

2. Multi-Level Orderbook (analysis_get_multi_level_orderbook):
   - Detailed bid/ask levels
   - Order book depth and liquidity
   - Price impact analysis
   - Best execution levels

3. Historical Trends (analysis_get_historical_trends):
   - Price history and trends
   - Volume patterns
   - News sentiment analysis
   - Market context and background

4. Market Trades (analysis_get_market_trades):
   - Recent trading activity
   - Trade size distribution
   - Price impact of trades
   - Trading patterns

5. External News (analysis_get_external_news):
   - Relevant news articles
   - Market sentiment indicators
   - External factors affecting the market

Analysis Process:
1. First gather all necessary market data using the available tools
2. Analyze each aspect of the market:
   - Price levels and trends
   - Liquidity and depth
   - Trading activity and patterns
   - Market sentiment and news impact
3. Look for correlations between different data points
4. Identify potential trading opportunities or risks
5. Provide a comprehensive analysis using the AnalysisInfo tool

Key Analysis Requirements:
1. Always check both sides of the orderbook for liquidity
2. Consider the impact of recent trades on market prices
3. Factor in external news and sentiment
4. Assess market efficiency and potential mispricing
5. Evaluate execution costs and optimal trade sizes
6. Consider the relationship between different outcomes

When you have completed your analysis:
1. Use the AnalysisInfo tool to provide a structured analysis
2. Include specific metrics and observations
3. Provide clear reasoning for your conclusions
4. Assign a confidence level to your analysis
5. Make specific recommendations for trade execution

Remember: Your analysis will be used to make trading decisions, so be thorough and precise."""

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

    data_check_prompt = "\nData Availability Status:\n"
    for data_type, is_available in required_data_checks.items():
        if not is_available:
            data_check_prompt += f"- {data_type}: NOT AVAILABLE - Please use appropriate tool to fetch this data\n"
        else:
            data_check_prompt += f"- {data_type}: Available\n"
    
    p += data_check_prompt

    messages = [SystemMessage(content=system_text)] + [HumanMessage(content=p)] + state.messages

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
    last_message = state.messages[-1] if state.messages else None
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
3. Basic market sentiment from recent activity
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
    user_has_positions = any(position_info.values())  # True if any positive size

    # The user can do NO_TRADE or BUY in all scenarios
    # The user can SELL only if they have an existing position
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
            "For binary markets, you must also specify which outcome (YES/NO) you want to trade. "
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
                "outcome": {
                    "type": "string",
                    "description": "For binary markets, specify which outcome to trade: YES or NO",
                    "enum": ["YES", "NO"]
                },
                "token_id": {
                    "type": "string",
                    "description": "The token ID for which the trade is being made (as a string)."
                },
                "market_id": {
                    "type": "string",
                    "description": "The market ID for which the trade is being made (as a string)."
                },
                "size": {
                    "type": "number",
                    "description": (
                        "The size (in USDC if buying, shares if selling) that the user should trade. "
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
                "size",
                "reason",
                "confidence",
                "outcome",
                "token_id"
            ]
        }
    }

    available_funds = poly_client.get_usdc_balance()

    # Build a comprehensive prompt that includes all available information
    system_text = f"""You are a trade decision maker. Your task is to make a SINGLE, CLEAR trade decision based on all available information.
You must use the trade tool ONCE to record your decision. Do not make multiple trade calls.

Available Information:
1. Market Data: {json.dumps(state.market_data or {}, indent=2)}
2. Research Report: {json.dumps(state.research_report or {}, indent=2)}
3. Analysis Info: {json.dumps(state.analysis_info or {}, indent=2)}
4. User Positions (for this or related markets): {json.dumps(state.positions or {}, indent=2)}
5. User's Available Funds for a new position: {available_funds}
6. Market Tokens: {[{"token_id": t.token_id, "outcome": t.outcome} for t in state.tokens] if state.tokens else []}

You MAY ONLY choose 'side' from this list: {possible_sides}.
For binary markets, you MUST specify which outcome (YES/NO) you want to trade.

If all of the values are not filled, you must fill them by using the tools at your disposal.

Required Fields:
- side: Must be one of {possible_sides}
- outcome: Must be either "YES" or "NO" for binary markets
- market_id: Must be a string
- size: Must be a number
- reason: Must be a non-empty string with clear reasoning
- confidence: Must be a number between 0 and 1

If the user does not hold any position in this market, you may NOT choose SELL. 
You can either buy or do no trade.

If the user already has a position, you can consider SELL as well.

Be sure to respect the user's 'available_funds' if you recommend buying. 
Do not propose a trade that exceeds these available funds.

When you have finalized your decision, call the TradeDecision tool exactly once.

Remember to be explicit about which outcome (YES/NO) you want to trade when making a decision.
Your reasoning should clearly explain why you chose that particular outcome.
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
            # Create and store TradeDecision object
            try:
                trade_decision_obj = TradeDecision(
                    side=trade_info.get("side"),
                    outcome=trade_info.get("outcome")
                )
                state.trade_decision = trade_decision_obj
            except ValueError as e:
                print(f"Invalid trade decision: {str(e)}")
                state.trade_decision = None
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
        "size": lambda x: isinstance(x, (int, float)),
        "outcome": lambda x: x in ["YES", "NO"] if x is not None else True  # Allow None only for NO_TRADE
    }

    system_text = """You are validating a trade decision. Your task is to ensure the decision is complete and properly formatted.

Required Fields:
- side: Must be one of "BUY", "SELL", "NO_TRADE"
- outcome: Must be "YES" or "NO" for binary markets when side is BUY or SELL
- market_id: Must be a string
- size: Must be a number
- reason: Must be a non-empty string with clear reasoning
- confidence: Must be a number between 0 and 1

The decision should be clear, well-reasoned, and based on the available market data and analysis.
If side=NO_TRADE, size can be 0 and outcome can be omitted.
If side=BUY, size must not exceed available funds.
If side=SELL, user must have a position in the market (though the LLM check is partial).

For binary markets:
1. The outcome must be specified as either YES or NO when buying or selling
2. The token_id must match the specified outcome
3. The reasoning must clearly explain why that specific outcome was chosen
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
            if field == "outcome" and trade_info.get("side") == "NO_TRADE":
                continue  # Skip outcome validation for NO_TRADE
            if value is None:
                is_valid = False
                validation_errors.append(f"Missing required field: {field}")
            elif not validator(value):
                is_valid = False
                validation_errors.append(f"Invalid value for {field}: {value}")

        # Additional checks
        side_val = trade_info.get("side", "")
        size_val = trade_info.get("size", 0)
        outcome_val = trade_info.get("outcome")

        available_funds = poly_client.get_usdc_balance()

        if side_val == "NO_TRADE" and size_val != 0:
            is_valid = False
            validation_errors.append("If side=NO_TRADE, size must be 0.")

        if side_val in ["BUY", "SELL"]:
            # Validate outcome is specified for binary markets
            if not outcome_val:
                is_valid = False
                validation_errors.append("Must specify YES or NO outcome when buying or selling.")

            # Find the correct token based on the outcome
            if state.tokens and outcome_val:
                token = next((t for t in state.tokens if t.outcome == outcome_val), None)
                if not token:
                    is_valid = False
                    validation_errors.append(f"No token found for outcome: {outcome_val}")
                else:
                    # Store the token_id in trade_info
                    state.trade_info["token_id"] = token.token_id

        if side_val == "BUY":
            if size_val is not None and size_val > available_funds:
                is_valid = False
                validation_errors.append(f"Cannot BUY with size {size_val} exceeding available funds {available_funds}.")
            
        if side_val == "SELL":
            if state.tokens and outcome_val:
                token = next((t for t in state.tokens if t.outcome == outcome_val), None)
                if token:
                    position_size = state.positions.get(token.token_id, 0)
                    if position_size <= 0:
                        is_valid = False
                        validation_errors.append(f"Cannot SELL {outcome_val} token - no position held.")
                    elif size_val > position_size:
                        is_valid = False
                        validation_errors.append(f"Cannot SELL {size_val} {outcome_val} tokens - only have {position_size}.")

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
    
async def save_trade_info_node(
    state: State,
    *,
    config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    """Save the trade info to the database."""
    return {
        "messages": [],
        "decision": "end"
    }

###############################################################################
# Node: Human Confirmation
###############################################################################
async def human_confirmation_node(
    state: State,
    *,
    config: Optional[RunnableConfig] = None
) -> Command[Literal["process_human_input", "__end__"]]:
    """
    This node waits for human confirmation before executing a trade.
    It only runs if the trade decision is BUY or SELL.
    """
    if not state.trade_info or state.trade_decision == "NO_TRADE":
        return {
            "messages": [],
            "decision": "end"
        }
    
    llm_output = f"""
    Trade Decision Summary:
    ----------------------
    Side: {state.trade_info.get('side')}
    Market ID: {state.trade_info.get('market_id')}
    Token ID: {state.trade_info.get('token_id')}
    Size: {state.trade_info.get('size')}
    Confidence: {state.trade_info.get('confidence')}

    Reasoning: {state.trade_info.get('reason')}

    Market Analysis: {state.trade_info.get('trade_evaluation_of_market_data')}
    """
    
    make_purchase = interrupt(
        {
        "question": "Do you want to proceed with this trade?",
        "llm_output": llm_output
        }
    )

    print("make_purchase: ", make_purchase)
    print("make_purchase['value']: ", make_purchase["value"])
    
    if make_purchase["value"] == "true":
        return Command(goto="process_human_input", update={"user_confirmation": True}) 
    else:
        return Command(goto="__end__", update={"user_confirmation": False})
    

async def human_confirmation_node_js(
    state: State,
    *,
    config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    """
    We are doing nothing in this node because the langgraph JS SDK does not support interrupting the graph.
    Thus, we are updating the state from the web app using the JS SDK.
    """
    pass

async def process_human_input_node(
    state: State,
    *,
    config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    """Process the human's response to the trade confirmation."""
    print("INSIDE PROCESS HUMAN INPUT NODE")

    if state.user_confirmation:
        # Execute the trade
        try:

            condition_id = state.market_data.get("condition_id")

            # Get trade parameters from state
            side = state.trade_info.get("side")
            token_id = state.trade_info.get("token_id")
            size = state.trade_info.get("size")

            print("condition_id: ", condition_id)
            print("side: ", side)
            print("token_id: ", token_id)
            print("size: ", size)

            # Create and execute the order
            if not state.debug:
                order_response = poly_client.execute_market_order(
                    token_id=token_id,
                    amount=size,
                    side=side
                )

                print("Order response: ", order_response)

                return {
                    "messages": [AIMessage(content=f"Trade executed successfully! Order response: {order_response}")],
                    "order_response": order_response,
                    "trade_info": state.trade_info,
                    "decision": "end"
                }
            else:
                print("DEBUG MODE: WOULD HAVE TRADED")
                return {
                    "messages": [AIMessage(content=f"DEBUG MODE: WOULD HAVE TRADED")],
                    "order_response": None,
                    "trade_info": state.trade_info,
                    "decision": "end"
                }
        except Exception as e:
            return {
                "messages": [AIMessage(content=f"Failed to execute trade: {str(e)}")],
                "decision": "end"
            }
    else:
        return {
            "messages": [AIMessage(content="Trade cancelled by user.")],
            "decision": "end"
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

def route_after_research_agent(state: State, config: Optional[RunnableConfig] = None) -> Literal["research_agent", "research_tools", "reflect_on_research", "__end__"]:
    """After research agent, check if we need to execute tools or reflect."""
    print("INSIDE ROUTE AFTER RESEARCH AGENT")
    last_msg = state.messages[-1]
    print("state.research_report: ", state.research_report)

    if state.loop_step > 3:
        return "__end__"

    # First check if we already have research results
    if state.research_report and not last_msg.additional_kwargs.get("improvement_instructions"):
        return "reflect_on_research"
    
    if state.research_report and last_msg.additional_kwargs.get("improvement_instructions") and last_msg.tool_calls[0]["name"] == "deep_research":
        return "research_tools"
        
    if not isinstance(last_msg, AIMessage):
        return "research_agent"
    
    if last_msg.tool_calls and last_msg.tool_calls[0]["name"] == "deep_research":
        return "research_tools"
    elif last_msg.tool_calls and last_msg.tool_calls[0]["name"] == "ExternalResearchInfo":
        return "reflect_on_research"
    else:
        return "research_agent"

def route_after_reflect_on_research(state: State, *, config: Optional[RunnableConfig] = None) -> Literal["research_agent", "analysis_agent", "__end__"]:
    configuration = Configuration.from_runnable_config(config)

    last_msg = state.messages[-1] if state.messages else None
    print("LAST MSG: ", last_msg)
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

def route_after_reflect_on_trade(state: State, *, config: Optional[RunnableConfig] = None) -> Literal["trade_agent", "human_confirmation", "human_confirmation_js", "__end__"]:
    """After reflection, either end the workflow or request a new trade decision."""
    configuration = Configuration.from_runnable_config(config)

    last_msg = state.messages[-1] if state.messages else None
    if not isinstance(last_msg, ToolMessage):
        return "trade_agent"
    
    if state.trade_info.get("side") in ["BUY", "SELL"]:
        if state.from_js:
            return "human_confirmation_js"
        else:
            return "human_confirmation"
    
    # If validation was successful, end the workflow
    if last_msg.status == "success":
        return "__end__"
    
    # If we've exceeded max loops, end anyway
    if state.loop_step >= configuration.max_loops:
        return "__end__"
    
    # Otherwise, try one more trade decision
    return "trade_agent"

def route_after_human_confirmation_js(state: State) -> Literal["process_human_input", "__end__"]:
    """Route after human confirmation node."""
    if state.user_confirmation:
        return "process_human_input"
    else:
        return "__end__"

###############################################################################
# Construct the Graph
###############################################################################
workflow = StateGraph(State, input=InputState, output=OutputState, config_schema=Configuration)


workflow.add_edge("__start__", "fetch_market_data")
workflow.add_node("fetch_market_data", fetch_market_data)
workflow.add_conditional_edges("fetch_market_data", route_after_fetch)

# Research 
workflow.add_node("research_tools", ToolNode([
    deep_research
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

# Update the routing after reflect_on_trade
workflow.add_node("human_confirmation", human_confirmation_node)
workflow.add_node("human_confirmation_js", human_confirmation_node_js)
workflow.add_node("process_human_input", process_human_input_node)

workflow.add_conditional_edges("human_confirmation_js", route_after_human_confirmation_js)

workflow.add_edge("process_human_input", "__end__")

# Set up memory
memory = MemorySaver()

# Compile
graph = workflow.compile(checkpointer=memory)
# graph = workflow.compile()
graph.name = "PolymarketAgent"