# <ai_context>
# This file defines external research tools for the Polymarket AI agent,
# such as TavilySearch, Exa, or web scraping. The agent can call these
# tools via LangChain or directly in the node functions in graph.py.
# </ai_context>

"""Tools for Polymarket trading agent.

This module contains functions that are directly exposed to the LLM as tools.
These tools can be used for tasks such as web searching and making trade decisions.
"""

from typing import Any, List, Optional, cast
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
from langchain_exa import ExaSearchResults

from polytrader.configuration import Configuration
from polytrader.state import State

async def search_tavily(
    query: str, 
    *, 
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[List[dict[str, Any]]]:
    """Perform a Tavily search to find relevant articles and information.
    
    This function queries Tavily to fetch comprehensive, accurate, and trusted results.
    Provide as much context in the query as needed to ensure high recall.
    """
    configuration = Configuration.from_runnable_config(config)
    tavily = TavilySearchResults(max_results=configuration.max_search_results)
    results = await tavily.arun(query)
    return cast(List[dict[str, Any]], results)

async def search_exa(
    query: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[List[dict[str, Any]]]:
    """Perform an Exa search to find relevant articles and information.
    
    This function queries Exa to fetch comprehensive, accurate, and trusted results.
    Provide as much context in the query as needed to ensure high recall.
    """
    configuration = Configuration.from_runnable_config(config)
    exa = ExaSearchResults(max_results=configuration.max_search_results)
    
    # Create the invoke arg
    invoke_arg = {"query": query, "num_results": configuration.max_search_results}
    
    # Get SearchResponse object
    response = exa.invoke(invoke_arg)
    
    # Extract and structure the results
    structured_results = []
    for result in response.results:
        structured_results.append({
            "title": result.title if hasattr(result, 'title') else "",
            "url": result.url if hasattr(result, 'url') else "",
            "id": result.id if hasattr(result, 'id') else "",
            "score": result.score if hasattr(result, 'score') else 0,
            "published_date": result.published_date if hasattr(result, 'published_date') else None,
            "author": result.author if hasattr(result, 'author') else None,
            "text": result.text if hasattr(result, 'text') else "",
            "highlights": result.highlights if hasattr(result, 'highlights') else [],
            "image": result.image if hasattr(result, 'image') else None,
            "favicon": result.favicon if hasattr(result, 'favicon') else None
        })
    
    return structured_results

async def trade(
    side: str,
    reason: str,
    confidence: float,
    *,
    state: Annotated[State, InjectedState],
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Finalize a trade decision.
    
    Args:
        side: The trade direction ('BUY YES', 'SELL', or 'HOLD')
        reason: A summary of the logic behind the trade
        confidence: Confidence level between 0 and 1
        state: The current state object
        config: The configuration object
    
    Returns:
        str: A confirmation message about the trade decision
    """
    # Store the trade decision in state
    state.trade_decision = side
    state.confidence = confidence
    
    return f"Trade decision finalized: {side} with confidence {confidence}. Reason: {reason}"

def structure_research(raw_text: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Structure the scraped research text into a given schema."""
    structured = dict(schema)  # copy
    structured["summary"] = raw_text[:200]
    structured["headline"] = "Sample Headline"
    structured["source_links"] = ["N/A"]
    return structured

# -------------------------------------------------------------------------
# Below we define standard "tool" dictionaries for LLM usage with .bind_tools(...)
# Each tool dict has a "name", "description", and "func" field at minimum.

search_tavily_tool = {
    "name": "search_tavily",
    "description": (
        "Perform a Tavily search with `query` to find articles. "
        "Argument must be a JSON object with `query` (string) "
        "and optionally `max_results` (int)."
    ),
    "func": search_tavily
}

search_exa_tool = {
    "name": "search_exa",
    "description": (
        "Perform an Exa search with `query` to find relevant results. "
        "Argument must be a JSON object with `query` (string) "
        "and optionally `max_results` (int)."
    ),
    "func": search_exa
}

# This is a "Trade" tool. The LLM calls it to finalize the trade decision.
trade_tool = {
    "name": "Trade",
    "description": (
        "Finalize your trade decision. Must provide arguments: "
        "`side` (string: 'BUY YES' | 'SELL' | 'HOLD'), "
        "`reason` (string summary of your logic), "
        "`confidence` (float, 0 <= c <= 1)."
    ),
    "parameters": {
        "side": "string",
        "reason": "string",
        "confidence": "number"
    }
}