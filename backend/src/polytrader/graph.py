# <ai_context>
# This file implements a stateful graph for the Polymarket AI agent using LangGraph.
# It orchestrates the following steps:
# 1) Fetch/refresh market data
# 2) Reflect on market data
# 3) Analyze external info (Tavily, Exa)
# 4) Reflect on external info
# 5) Make a trade decision (using the LLM)
# 6) Reflect on the decision
# 7) End or loop back as needed
#
# </ai_context>

import ast
import time
from typing import Any, Dict, Literal

from langchain.schema import HumanMessage, SystemMessage

# Use the recommended import from langchain_community
from langchain_community.chat_models import ChatOpenAI

# langgraph imports
from langgraph.graph import StateGraph

from polytrader.configuration import Configuration

# Polymarket
from polytrader.gamma import GammaMarketClient
from polytrader.polymarket import Polymarket

# Our new state, configuration, and tools
from polytrader.state import InputState, OutputState, State
from polytrader.tools import scrape_website, search_tavily, structure_research

###############################################################################
# Global references
###############################################################################
gamma_client = GammaMarketClient()
poly_client = Polymarket()

# Create a default config. Real usage might override via environment or a constructor.
config = Configuration()
llm = ChatOpenAI(model_name=config.model, temperature=config.temperature)


###############################################################################
# 1. Node: Fetch Market Data
###############################################################################
async def fetch_market_data(state: State) -> Dict[str, Any]:
    """Fetch or refresh data from Gamma about the specified market_id."""
    state.loop_step += 1
    market_id = state.market_id

    markets_json = gamma_client.get_current_markets(1)
    market_json = markets_json[0]

    if market_id is None:
        return {
            "messages": ["No market_id provided; skipping market data fetch."],
            "proceed": False,
        }

    # Use GammaMarketClient to fetch data
    # market_json = gamma_client.get_market(market_id)
    state.market_data = market_json  # raw dict
    return {
        "messages": [f"Fetched market data for ID={market_id}."],
        "proceed": True,
        "market_data": market_json,
    }


###############################################################################
# 2. Node: Reflect on Market Data
###############################################################################
async def reflect_on_market_data(state: State) -> Dict[str, Any]:
    """Check if the market data is good enough to proceed or if we need to refetch/stop."""
    if not state.market_data:
        return {
            "messages": ["No market data found. Need to re-fetch."],
            "proceed": False,
        }
    if "question" not in state.market_data:
        return {
            "messages": [
                "Market data doesn't have a question field. Might be incomplete."
            ],
            "proceed": False,
        }
    return {"messages": ["Market data looks sufficient."], "proceed": True}


###############################################################################
# 3. Node: Analyze External Info (Tavily + scraping)
###############################################################################
async def analyze_external_info(state: State) -> Dict[str, Any]:
    """Use an external research tool (Tavily) to gather data, then scrape the top result."""
    state.loop_step += 1

    query = "Polymarket " + (
        state.market_data.get("question", "Generic search") if state.market_data else ""
    )
    results = await search_tavily(query, max_results=config.max_search_results)
    if not results:
        return {
            "messages": [f"Tavily returned no search results for query: {query}"],
            "proceed": False,
        }

    first_url = results[0].get("link", "")
    if not first_url:
        return {
            "messages": ["No valid link in the top search result."],
            "proceed": False,
        }

    scraped_content = await scrape_website(first_url)
    structured = structure_research(scraped_content, state.extraction_schema)
    state.external_research = structured

    return {
        "messages": [
            f"Analyzed external info with query='{query}'.",
            f"Scraped URL: {first_url}",
        ],
        "external_research": structured,
        "proceed": True,
    }


###############################################################################
# 4. Node: Reflect on External Info
###############################################################################
async def reflect_on_external_info(state: State) -> Dict[str, Any]:
    """Decide if the external research is sufficient or needs re-analysis."""
    if not state.external_research:
        return {
            "messages": ["No external research found. Need to gather again."],
            "proceed": False,
        }
    summary = state.external_research.get("summary", "")
    if not summary:
        return {
            "messages": ["External info is incomplete, no summary found."],
            "proceed": False,
        }
    return {"messages": ["External research is sufficient."], "proceed": True}


###############################################################################
# 5. Node: Decide Trade using LLM
###############################################################################
async def decide_trade(state: State) -> Dict[str, Any]:
    """Use the LLM to reason about the market data and external info and produce a trade decision."""
    state.loop_step += 1
    market_data_str = str(state.market_data)
    external_info_str = str(state.external_research)

    prompt = [
        SystemMessage(
            content="You are a Polymarket trading AI. You have market data and external research."
        ),
        HumanMessage(
            content=(
                f"Market data: {market_data_str}\n\n"
                f"External research: {external_info_str}\n\n"
                "Decide whether to BUY, SELL, or HOLD. "
                "Write your decision in plain text, e.g. 'BUY YES' or 'SELL' or 'HOLD'."
            )
        ),
    ]
    response = await llm.apredict(prompt)
    decision_text = response.strip().upper()

    if "BUY" in decision_text:
        state.trade_decision = "BUY YES"
    elif "SELL" in decision_text:
        state.trade_decision = "SELL"
    else:
        state.trade_decision = "HOLD"

    return {
        "messages": [f"LLM suggests decision: {state.trade_decision}"],
        "trade_decision": state.trade_decision,
        "proceed": True,
    }


###############################################################################
# 6. Node: Reflect on the Decision (and possibly place an order)
###############################################################################
async def reflect_on_decision(state: State) -> Dict[str, Any]:
    """Reflect on the final decision. If it's BUY or SELL, place an actual order on Polymarket."""
    decision = state.trade_decision
    if not decision or decision == "HOLD":
        return {
            "messages": ["Decision is HOLD or not set. Not placing any trades."],
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
        clob_token_ids = ast.literal_eval(clob_token_ids)
    if not clob_token_ids:
        return {
            "messages": ["No token IDs in market data. Skipping trade."],
            "proceed": False,
        }

    yes_token_id = clob_token_ids[0]
    side = "BUY" if decision.startswith("BUY") else "SELL"
    size = 10
    poly_client.execute_order(
        price=0.5, size=size, side=side, token_id=yes_token_id
    )

    return {
        "messages": [
            f"Placed a {decision} order on token_id={yes_token_id} for size={size}."
        ],
        "proceed": True,
    }


###############################################################################
# 7. Routing Logic
###############################################################################
def route_after_market_data(state: State) -> Literal["reflect_on_market_data"]:
    """Route after market data."""
    return "reflect_on_market_data"


def route_after_market_reflection(
    state: State,
) -> Literal["analyze_external_info", "fetch_market_data", "__end__"]:
    """Route after reflecting on market data."""
    proceed = False
    if state.market_data and "question" in state.market_data:
        proceed = True

    if not proceed and state.loop_step < config.max_loops:
        return "fetch_market_data"
    elif not proceed:
        return "__end__"
    else:
        return "analyze_external_info"


def route_after_external_info(state: State) -> Literal["reflect_on_external_info"]:
    """Route after external info is analyzed."""
    return "reflect_on_external_info"


def route_after_external_reflection(
    state: State,
) -> Literal["decide_trade", "analyze_external_info", "__end__"]:
    """Route after reflecting on external info."""
    proceed = False
    if state.external_research and state.external_research.get("summary"):
        proceed = True

    if not proceed and state.loop_step < config.max_loops:
        return "analyze_external_info"
    elif not proceed:
        return "__end__"
    else:
        return "decide_trade"


def route_after_decision(state: State) -> Literal["reflect_on_decision"]:
    """Route after deciding a trade action."""
    return "reflect_on_decision"


def route_after_decision_reflection(
    state: State,
) -> Literal["__end__", "fetch_market_data"]:
    """Route after reflecting on the trade decision."""
    if (
        state.trade_decision == "HOLD" or not state.trade_decision
    ) and state.loop_step < config.max_loops:
        return "fetch_market_data"
    return "__end__"


###############################################################################
# Construct the Graph
###############################################################################
workflow = StateGraph(
    State,
    input=InputState,
    output=OutputState,
)

# Add nodes
workflow.add_node(fetch_market_data)
workflow.add_node(reflect_on_market_data)
workflow.add_node(analyze_external_info)
workflow.add_node(reflect_on_external_info)
workflow.add_node(decide_trade)
workflow.add_node(reflect_on_decision)

# Edges
workflow.add_edge("__start__", "fetch_market_data")
workflow.add_conditional_edges("fetch_market_data", route_after_market_data)
workflow.add_conditional_edges("reflect_on_market_data", route_after_market_reflection)
workflow.add_conditional_edges("analyze_external_info", route_after_external_info)
workflow.add_conditional_edges(
    "reflect_on_external_info", route_after_external_reflection
)
workflow.add_conditional_edges("decide_trade", route_after_decision)
workflow.add_conditional_edges("reflect_on_decision", route_after_decision_reflection)

# Compile
graph = workflow.compile()
graph.name = "PolymarketAgent"