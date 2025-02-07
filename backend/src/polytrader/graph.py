# <ai_context>
# This file implements a stateful graph for the Polymarket AI agent using LangGraph.
# It orchestrates the following steps:
# 1) Fetch/refresh market data
# 2) Then delegates to an LLM-based node with tool usage
# 3) The LLM can call external info tools or finalize a trade via "Trade" tool
# 4) Reflect on the final decision
# 5) End or loop back as needed
# </ai_context>

import ast
import json
import time
from typing import Any, Dict, Literal, Optional, cast

from langchain.schema import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from polytrader.configuration import Configuration
from polytrader.gamma import GammaMarketClient
from polytrader.polymarket import Polymarket
from polytrader.state import InputState, OutputState, State
from polytrader.tools import (
    search_tavily,
    search_exa,
    trade,
)
from polytrader.utils import init_model

###############################################################################
# Global references
###############################################################################
gamma_client = GammaMarketClient()
poly_client = Polymarket()

###############################################################################
# 1. Node: Fetch Market Data
###############################################################################
async def fetch_market_data(state: State) -> Dict[str, Any]:
    """
    Fetch or refresh data from Gamma about the specified market_id.
    This remains as an initial step in the chain, storing raw JSON in state.
    """
    state.loop_step += 1
    market_id = state.market_id

    if market_id is None:
        return {
            "messages": ["No market_id provided; skipping market data fetch."],
            "proceed": False,
        }

    # Use GammaMarketClient to fetch data
    market_json = gamma_client.get_market(market_id)
    state.market_data = market_json  # raw dict
    print("Raw market data as json:")
    print(json.dumps(market_json, indent=2))
    return {
        "messages": [f"Fetched market data for ID={market_id}."],
        "proceed": True,
        "market_data": market_json,
    }

###############################################################################
# 2. Node: call_agent_model
###############################################################################
async def call_agent_model(
    state: State, *, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
    """
    Primary LLM node that uses tools for external research or finalizing trades.
    This is analogous to your example "call_agent_model" approach.
    """
    # Grab config
    configuration = Configuration.from_runnable_config(config)

    # Prepare a system message, giving context about the Polymarket scenario
    system_content = (
        "You are a Polymarket trading AI. You have access to the raw market data below.\n\n"
        "You can call any of the provided tools to get more information or finalize a trade.\n"
        "When you are ready to finalize your decision, call the 'Trade' tool.\n"
    )
    market_data_str = json.dumps(state.market_data or {}, indent=2)
    system_msg = SystemMessage(content=f"{system_content}\nMarket Data:\n{market_data_str}")

    # Add any prior conversation from state.messages
    # Usually, we put the system message at the front.
    # Then we append the conversation messages.
    messages: list[BaseMessage] = [system_msg] + state.messages

    # Initialize raw model
    raw_model = init_model(config)

    # Bind our tools. We have two search tools + one "Trade" tool.
    # tool_choice="any" means the LLM can call them by name.
    model = raw_model.bind_tools(
        [search_exa, search_tavily, trade],
        tool_choice="any"
    )

    # Invoke model
    response = cast(AIMessage, await model.ainvoke(messages))

    # We'll capture the new response as part of the conversation
    response_messages: list[BaseMessage] = [response]

    # Check if the model tried to call any tools
    trade_submitted = None
    if response.tool_calls:
        for tc in response.tool_calls:
            # If it's the "Trade" tool, parse the arguments
            if tc["name"] == "Trade":
                # The LLM is finalizing
                trade_submitted = tc["args"]
                break

    if trade_submitted is not None:
        # Store the trade decision in state
        # e.g. side='BUY YES', reason='my logic', confidence=0.8
        state.trade_decision = trade_submitted["side"]
        # We'll store the confidence as well
        state.confidence = float(trade_submitted["confidence"])
        # Provide a short message about it
        response_messages.append(
            ToolMessage(
                tool_call_id=tc["id"],
                content=f"Finalized trade: {state.trade_decision}, confidence={state.confidence}",
                name="Trade",
                status="success",
            )
        )

    # Return the messages to store in state
    return {
        "messages": response_messages,
        "proceed": True,
        "loop_step": state.loop_step + 1,
    }

###############################################################################
# 3. Node: tools
###############################################################################
tools_node = ToolNode([search_tavily, search_exa, trade])

###############################################################################
# 4. Node: reflect_on_decision
###############################################################################
async def reflect_on_decision(state: State) -> Dict[str, Any]:
    """
    Reflect on the final decision. If it's BUY or SELL, place an actual order on Polymarket.
    If HOLD or no decision, do nothing. This is where we handle the actual trading side effect.
    """
    decision = state.trade_decision
    if not decision:
        return {
            "messages": ["No final trade decision set. Possibly the model never called Trade."],
            "proceed": False,
        }

    if decision.upper().startswith("BUY"):
        side = "BUY"
    elif decision.upper().startswith("SELL"):
        side = "SELL"
    else:
        side = "HOLD"

    if side == "HOLD":
        return {
            "messages": ["Decision is HOLD. Not placing any trades."],
            "proceed": False,
        }

    if not state.market_data or not state.market_data.get("clobTokenIds"):
        return {
            "messages": [
                "No market_data.clobTokenIds found, cannot place trade. Holding."
            ],
            "proceed": False,
        }

    clob_token_ids = state.market_data["clobTokenIds"]
    if isinstance(clob_token_ids, str):
        try:
            clob_token_ids = ast.literal_eval(clob_token_ids)
        except Exception:
            pass
    if not clob_token_ids or not isinstance(clob_token_ids, list):
        return {
            "messages": ["No token IDs in market data. Skipping trade."],
            "proceed": False,
        }

    yes_token_id = clob_token_ids[0]
    size = 10  # Hard-coded example
    poly_client.execute_order(price=0.5, size=size, side=side, token_id=yes_token_id)

    return {
        "messages": [
            f"Placed a {side} order on token_id={yes_token_id} for size={size}."
        ],
        "proceed": True,
    }

###############################################################################
# Old nodes commented out or deprecated:
###############################################################################
# async def analyze_external_info(state: State) -> Dict[str, Any]:
#     """
#     Deprecated. Replaced by letting the LLM call search tools directly.
#     """
#     return {}

# async def reflect_on_external_info(state: State) -> Dict[str, Any]:
#     """
#     Deprecated. 
#     """
#     return {}

# async def decide_trade(state: State) -> Dict[str, Any]:
#     """
#     Deprecated, replaced by call_agent_model approach.
#     """
#     return {}

# async def assess_confidence(state: State) -> Dict[str, Any]:
#     """
#     Deprecated, replaced by agent tool calls.
#     """
#     return {}

###############################################################################
# 5. Routing logic
###############################################################################
def route_after_fetch(state: State) -> Literal["call_agent_model", "__end__"]:
    """
    After we fetch market data, proceed to call_agent_model unless there's no data or 'proceed' is False.
    """
    if not state.market_data:
        return "__end__"
    return "call_agent_model"

def route_after_call_agent(state: State) -> Literal["tools", "reflect_on_decision", "call_agent_model", "__end__"]:
    """
    If the LLM used a tool, route to tools node. If it finalized trade, reflect on decision.
    Otherwise loop more or end if max steps reached.
    """
    last_message = state.messages[-1] if state.messages else None
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        # Check if it's the Trade tool
        if last_message.tool_calls[0]["name"] == "Trade":
            return "reflect_on_decision"
        # Otherwise we assume it called search_exa / search_tavily
        return "tools"

    # If no tool call, we can keep asking the model again, unless we exceed loops
    configuration = Configuration.from_runnable_config()
    if state.loop_step >= configuration.max_loops:
        return "__end__"

    return "call_agent_model"

def route_after_tools(state: State) -> Literal["call_agent_model"]:
    """
    After we run the requested tool, route back to call_agent_model to continue.
    """
    return "call_agent_model"

def route_after_reflection(state: State) -> Literal["__end__", "call_agent_model"]:
    """
    If the reflection is done, we can end. But if we want to continue for some reason, do it here.
    We'll just end by default.
    """
    return "__end__"

###############################################################################
# Construct the Graph
###############################################################################
workflow = StateGraph(State, input=InputState, output=OutputState, config_schema=Configuration)

# Add nodes
workflow.add_node(fetch_market_data)
workflow.add_node(call_agent_model)
workflow.add_node("tools", tools_node)
workflow.add_node(reflect_on_decision)

# Edges
workflow.add_edge("__start__", "fetch_market_data")
workflow.add_conditional_edges("fetch_market_data", route_after_fetch)
workflow.add_conditional_edges("call_agent_model", route_after_call_agent)
workflow.add_conditional_edges("tools", route_after_tools)
workflow.add_conditional_edges("reflect_on_decision", route_after_reflection)

# Compile
graph = workflow.compile()
graph.name = "PolymarketAgent"