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
    # analysis_get_external_news,  # REMOVED from analysis agent
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

    market_json = gamma_client.get_market(market_id)
    state.market_data = market_json  # raw dict
    print("Raw market data as json:")
    print(json.dumps(market_json, indent=2))
    return {
        "messages": [f"Fetched market data for ID={market_id}."],
        "proceed": True,
        "market_data": market_json,
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
        search_tavily,
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
    system_text = """You are evaluating the quality of research gathered about a market.
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
                )            ],
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

    trade_prompt_schema = {
        "side": "",
        "reason": "",
        "confidence": 0.0
    }

    system_text = configuration.trade_agent_prompt.format(
        info=json.dumps(trade_prompt_schema, indent=2),
        market_data=json.dumps(state.market_data or {}, indent=2),
        question=state.market_data["question"],
        description=state.market_data["description"],
        outcomes=state.market_data["outcomes"]
    )

    messages = [HumanMessage(content=system_text)] + state.messages

    raw_model = init_model(config)
    # Bind the 'trade' function directly
    model = raw_model.bind_tools([trade], tool_choice="any")

    response = await model.ainvoke(messages)
    if not isinstance(response, AIMessage):
        response = AIMessage(content=str(response))

    trade_info = None
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["name"] == "trade":
                trade_info = tool_call["args"]
                break
        if trade_info is not None:
            response.tool_calls = [
                tc for tc in response.tool_calls if tc["name"] == "trade"
            ]

    new_messages: List[BaseMessage] = [response]
    if not response.tool_calls:
        new_messages.append(
            HumanMessage(content="Please respond by calling the 'trade' tool to finalize your decision.")
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
    This node checks if the trade decision is satisfactory.
    It uses a structured output model to evaluate the quality of the trade decision.
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"{reflect_on_trade_node.__name__} expects the last message in the state to be an AI message."
            f" Got: {type(last_message)}"
        )

    market_data_str = json.dumps(state.market_data or {}, indent=2)
    system_text = """You are evaluating the quality of a trade decision.
Your role is to determine if the trade decision is well-reasoned and ready to execute.
"""
    system_msg = SystemMessage(content=f"{system_text}\n\nMarket data:\n{market_data_str}")

    messages = [system_msg] + state.messages[:-1]
    
    trade_info = state.trade_info
    checker_prompt = """I am evaluating the trade decision below. 
Is this a well-reasoned trade decision ready to execute? Give your reasoning.
Consider factors like risk/reward, position size, and market timing.
If you don't think it's ready, be specific about what needs to be reconsidered.

Trade Decision:
{trade_info}"""
    
    p1 = checker_prompt.format(trade_info=json.dumps(trade_info or {}, indent=2))
    messages.append(HumanMessage(content=p1))

    raw_model = init_model(config)
    bound_model = raw_model.with_structured_output(TradeIsSatisfactory)
    response = cast(TradeIsSatisfactory, await bound_model.ainvoke(messages))

    if response.is_satisfactory and trade_info:
        return {
            "trade_info": trade_info,
            "messages": [
                ToolMessage(
                    tool_call_id=last_message.tool_calls[0]["id"] if last_message.tool_calls else "",
                    content="\n".join(response.reason),
                    name="Trade",
                    additional_kwargs={"artifact": response.model_dump()},
                    status="success",
                )
            ],
            "decision": "end"
        }
    else:
        return {
            "messages": [
                ToolMessage(
                    tool_call_id=last_message.tool_calls[0]["id"] if last_message.tool_calls else "",
                    content=f"Trade decision needs improvement:\n{response.improvement_instructions}",
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

def route_after_trade(state: State) -> Literal["trade_agent", "trade_tools", "reflect_on_trade"]:
    """After trade agent, check if we need to execute tools or reflect."""
    last_msg = state.messages[-1] if state.messages else None
    
    if not isinstance(last_msg, AIMessage):
        return "trade_agent"
    
    if last_msg.tool_calls and last_msg.tool_calls[0]["name"] == "Trade":
        return "reflect_on_trade"
    else:
        return "trade_tools"

def route_after_reflect_on_trade(state: State, *, config: Optional[RunnableConfig] = None) -> Literal["trade_agent", "__end__"]:
    configuration = Configuration.from_runnable_config(config)

    last_msg = state.messages[-1] if state.messages else None
    if not isinstance(last_msg, ToolMessage):
        return "trade_agent"
    
    if last_msg.status == "success":
        return "__end__"
    elif last_msg.status == "error":
        if state.loop_step >= configuration.max_loops:
            return "__end__"
        return "trade_agent"
    
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
    search_tavily
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

# Compile
graph = workflow.compile()
graph.name = "PolymarketAgent"