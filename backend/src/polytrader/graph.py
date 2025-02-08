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
    search_exa,
    search_tavily,
    market_details_tool,
    orderbook_analysis_tool,
    trade_tool,
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
    Sub-agent that focuses on Polymarket analysis.
    This node interprets market data and orderbook information.
    """
    configuration = Configuration.from_runnable_config(config)

    # Define the 'AnalysisInfo' tool for finalizing analysis
    analysis_info_tool = {
        "name": "AnalysisInfo",
        "description": "Call this when you have completed your analysis. Provide a summary, confidence (0-1), and any sources used.",
        "parameters": {
            "type": "object",
            "properties": {
                "analysis_summary": {
                    "type": "string",
                    "description": "A comprehensive summary of the market analysis findings"
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence level in the analysis (0-1)"
                },
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of sources or data references used in analysis"
                }
            },
            "required": ["analysis_summary", "confidence", "sources"]
        }
    }

    # Build the prompt
    p = configuration.analysis_agent_prompt.format(
        info=json.dumps({"analysis_summary": "", "confidence": 0.0, "sources": []}, indent=2),
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
        market_details_tool["func"],
        orderbook_analysis_tool["func"],
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

    response_messages: List[BaseMessage] = [response]
    if not response.tool_calls:  # If LLM didn't call any tool
        response_messages.append(
            HumanMessage(content="Please respond by calling one of the provided tools.")
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
    system_text = """You are evaluating the quality of market analysis.
Your role is to determine if the analysis is sufficient to proceed with trading decisions.
"""
    system_msg = SystemMessage(content=f"{system_text}\n\nMarket data:\n{market_data_str}")

    messages = [system_msg] + state.messages[:-1]
    
    analysis_info = state.analysis_info
    checker_prompt = """I am evaluating the market analysis information below. 
Is this sufficient to proceed with trading decisions? Give your reasoning.
Consider factors like market depth, liquidity analysis, and price trends.
If you don't think it's sufficient, be specific about what needs to be improved.

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
    # We'll reuse the existing trade_tool
    model = raw_model.bind_tools([trade_tool["func"]], tool_choice="any")

    response = await model.ainvoke(messages)
    if not isinstance(response, AIMessage):
        response = AIMessage(content=str(response))

    trade_info = None
    if response.tool_calls:
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
    return "research_agent"

def route_after_research_agent(state: State) -> Literal["research_agent", "research_tools", "reflect_on_research"]:
    """After research agent, check if we need to execute tools or reflect."""
    print("INSIDE ROUTE AFTER RESEARCH AGENT")
    last_msg = state.messages[-1]
    print(last_msg)
    
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
    market_details_tool,
    orderbook_analysis_tool["func"]
]))
workflow.add_node("analysis_agent", analysis_agent_node)
workflow.add_node("reflect_on_analysis", reflect_on_analysis_node)
workflow.add_conditional_edges("analysis_agent", route_after_analysis)
workflow.add_edge("analysis_tools", "analysis_agent")
workflow.add_conditional_edges("reflect_on_analysis", route_after_reflect_on_analysis)

# Trade
workflow.add_node("trade_tools", ToolNode([
    trade_tool["func"]
]))
workflow.add_node("trade_agent", trade_agent_node)
workflow.add_node("reflect_on_trade", reflect_on_trade_node)
workflow.add_edge("trade_tools", "trade_agent")
workflow.add_conditional_edges("trade_agent", route_after_trade)
workflow.add_conditional_edges("reflect_on_trade", route_after_reflect_on_trade)

# Compile
graph = workflow.compile()
graph.name = "PolymarketAgent"