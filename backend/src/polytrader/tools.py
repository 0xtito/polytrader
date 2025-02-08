# <ai_context>
# This file defines external research tools for the Polymarket AI agent,
# such as TavilySearch, Exa, or web scraping. The agent can call these
# tools via LangChain or directly in the node functions in graph.py.
# </ai_context>

"""Tools for Polymarket trading agent.

This module contains functions that are directly exposed to the LLM as tools.
These tools can be used for tasks such as web searching, market research and making trade decisions.
"""

import ast
import json
import logging
from typing import Any, List, Optional, cast, Dict
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
from langchain_exa import ExaSearchResults
from langchain.schema import SystemMessage, AIMessage
from langchain_core.messages import ToolMessage


from polytrader.configuration import Configuration
from polytrader.state import State
from polytrader.gamma import GammaMarketClient
from polytrader.polymarket import Polymarket
from polytrader.utils import init_model

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
gamma_client = GammaMarketClient()
poly_client = Polymarket()

async def get_market_details(
    market_id: str,
    *,
    state: Annotated[State, InjectedState],
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Get detailed information about a specific market.
    
    Args:
        market_id: The ID of the market to get details for
        state: The current state object
        config: The configuration object
    
    Returns:
        dict: Detailed market information including:
        - Current prices for YES/NO outcomes
        - Market question and description
        - Market status (active, funded, etc)
        - Volume and liquidity metrics
        - Token IDs for trading
    """
    logger.info(f"Fetching market details for market_id={market_id}")
    
    market_data = gamma_client.get_market(market_id)
    logger.info(f"Raw market data received: {json.dumps(market_data, indent=2)}")
    
    # Parse the outcome prices if they exist
    if "outcomePrices" in market_data:
        try:
            market_data["outcomePrices"] = ast.literal_eval(str(market_data["outcomePrices"]))
            logger.info(f"Parsed outcome prices: {market_data['outcomePrices']}")
        except Exception as e:
            logger.warning(f"Failed to parse outcome prices: {e}")

    # Add additional market metrics
    if "clobTokenIds" in market_data:
        try:
            token_ids = ast.literal_eval(str(market_data["clobTokenIds"]))
            if token_ids:
                # Get current prices from orderbook for each token
                current_prices = []
                for token_id in token_ids:
                    try:
                        price = poly_client.get_orderbook_price(token_id)
                        current_prices.append(price)
                        logger.info(f"Current price for token_id={token_id}: {price}")
                    except Exception as e:
                        logger.warning(f"Failed to get price for token_id={token_id}: {e}")
                        current_prices.append(None)
                market_data["current_market_prices"] = current_prices
                logger.info(f"Current market prices: {current_prices}")
        except Exception as e:
            logger.warning(f"Failed to process token IDs: {e}")
            
    # Log key market metrics for decision making
    logger.info("\nKey Market Metrics:")
    logger.info(f"Market Question: {market_data.get('question', 'N/A')}")
    logger.info(f"Market Status: Active={market_data.get('active', False)}, Funded={market_data.get('funded', False)}")
    logger.info(f"Current Prices: {market_data.get('current_market_prices', 'N/A')}")
    logger.info(f"Historical Prices: {market_data.get('outcomePrices', 'N/A')}")
            
    return market_data

async def get_orderbook_analysis(
    token_id: str,
    *,
    state: Annotated[State, InjectedState],
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Analyze the orderbook for a specific market token.
    
    Args:
        token_id: The token ID to analyze
        state: The current state object
        config: The configuration object
    
    Returns:
        dict: Comprehensive orderbook analysis including:
        - Best bid/ask prices
        - Bid/ask spread
        - Order book depth and liquidity
        - Volume metrics
        - Price trends
    """
    logger.info(f"\nAnalyzing orderbook for token_id={token_id}")
    
    try:
        # Get full orderbook data
        orderbook = poly_client.get_orderbook(token_id)
        best_price = poly_client.get_orderbook_price(token_id)
        logger.info(f"Retrieved orderbook data. Best price: {best_price}")
        logger.info(f"Full orderbook: {json.dumps(orderbook, indent=2)}")
        
        # Calculate key metrics
        analysis = {
            "token_id": token_id,
            "best_price": best_price,
            "liquidity": {
                "bid_depth": sum(order.get("size", 0) for order in orderbook.get("bids", [])),
                "ask_depth": sum(order.get("size", 0) for order in orderbook.get("asks", [])),
                "spread": None,
                "is_liquid": False
            },
            "orderbook": {
                "bids": orderbook.get("bids", [])[:5],  # Top 5 bids
                "asks": orderbook.get("asks", [])[:5]   # Top 5 asks
            }
        }
        
        # Calculate spread if possible
        if orderbook.get("bids") and orderbook.get("asks"):
            best_bid = float(orderbook["bids"][0].get("price", 0))
            best_ask = float(orderbook["asks"][0].get("price", 0))
            spread = best_ask - best_bid
            analysis["liquidity"]["spread"] = spread
            logger.info(f"Order book spread: {spread}")
            
        # Determine if market is liquid
        total_depth = (analysis["liquidity"]["bid_depth"] + 
                      analysis["liquidity"]["ask_depth"])
        analysis["liquidity"]["is_liquid"] = total_depth > 1000  # Example threshold
        
        # Log detailed liquidity analysis
        logger.info("\nLiquidity Analysis:")
        logger.info(f"Total Depth: {total_depth}")
        logger.info(f"Bid Depth: {analysis['liquidity']['bid_depth']}")
        logger.info(f"Ask Depth: {analysis['liquidity']['ask_depth']}")
        logger.info(f"Is Liquid: {analysis['liquidity']['is_liquid']}")
        logger.info(f"Best Bid: {best_bid if 'best_bid' in locals() else 'N/A'}")
        logger.info(f"Best Ask: {best_ask if 'best_ask' in locals() else 'N/A'}")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze orderbook: {e}")
        return {
            "error": f"Failed to analyze orderbook: {str(e)}",
            "token_id": token_id,
            "best_price": None,
            "liquidity": None,
            "orderbook": None
        }

async def search_tavily(
    query: str, 
    *, 
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[list[dict[str, Any]]]:
    """Perform a Tavily search to find relevant articles and information."""
    logger.info(f"\nPerforming Tavily search with query: {query}")
    
    configuration = Configuration.from_runnable_config(config)
    tavily = TavilySearchResults(max_results=configuration.max_search_results)
    results = await tavily.ainvoke(query)
    
    # Format results for tool message
    formatted_results = []
    for idx, result in enumerate(results):
        formatted_result = {
            "title": result.get("title", "N/A"),
            "url": result.get("url", "N/A"),
            "content": result.get("content", "N/A"),
            "score": result.get("score", "N/A"),
            "published_date": result.get("published_date", "N/A")
        }
        formatted_results.append(formatted_result)
        
    # Log search results
    logger.info(f"Found {len(formatted_results)} results from Tavily")

    return cast(list[dict[str, Any]], formatted_results)
    
    # return {
    #     "results": formatted_results,
    #     "query": query,
    #     "source": "tavily"
    # }

async def search_exa(
    query: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[list[dict[str, Any]]]:
    """Perform an Exa search to find relevant articles and information."""
    # logger.info(f"\nPerforming Exa search with query: {query}")
    print("INSIDE SEARCH EXA")
    
    configuration = Configuration.from_runnable_config(config)
    exa = ExaSearchResults(max_results=configuration.max_search_results)
    
    # Create the invoke arg
    invoke_arg = {"query": query, "num_results": configuration.max_search_results}
    
    # Get SearchResponse object
    response = await exa.ainvoke(invoke_arg)

    print("RESPONSE:")
    print(response)
    
    # Extract and structure the results
    formatted_results = []
    for result in response.results:
        formatted_result = {
            "title": result.title if hasattr(result, 'title') else "",
            "url": result.url if hasattr(result, 'url') else "",
            "content": result.text if hasattr(result, 'text') else "",
            "score": result.score if hasattr(result, 'score') else 0,
            "published_date": result.published_date if hasattr(result, 'published_date') else None
        }
        formatted_results.append(formatted_result)
        
    # Log search results
    logger.info(f"Found {len(formatted_results)} results from Exa")

    return cast(list[dict[str, Any]], formatted_results)
    
    # return {
    #     "results": formatted_results,
    #     "query": query,
    #     "source": "exa"
    # }

async def trade(
    side: str,
    reason: str,
    confidence: float,
    *,
    state: Annotated[State, InjectedState],
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Finalize a trade decision."""
    logger.info("\n=== Trade Decision Analysis ===")
    
    # Format the trade decision
    trade_decision = {
        "side": side,
        "confidence": confidence,
        "reason": reason,
        "market_context": {
            "market_id": state.market_data.get("id") if state.market_data else None,
            "question": state.market_data.get("question") if state.market_data else None,
            "current_prices": state.market_data.get("current_market_prices") if state.market_data else None
        }
    }
    
    # Store in state
    state.trade_decision = side
    state.confidence = confidence
    
    # Log decision
    logger.info(f"Trade Decision: {side}")
    logger.info(f"Confidence: {confidence}")
    logger.info(f"Reasoning: {reason}")
    
    return trade_decision

def structure_research(raw_text: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Structure the scraped research text into a given schema."""
    structured = dict(schema)  # copy
    structured["summary"] = raw_text[:200]
    structured["headline"] = "Sample Headline"
    structured["source_links"] = ["N/A"]
    return structured

# Below we define standard "tool" dictionaries for LLM usage with .bind_tools(...)
# Each tool dict has a "name", "description", and "func" field at minimum.

# Research tools
search_tavily_tool = {
    "name": "search_tavily",
    "description": (
        "Perform a Tavily search with `query` to find articles. "
        "Provide a search query to find relevant information."
    ),
    "func": search_tavily,
    "parameters": {
        "query": "string",
    }
}

search_exa_tool = {
    "name": "search_exa",
    "description": (
        "Perform an Exa search with `query` to find relevant results. "
        "Provide a search query to find relevant information."
    ),
    "func": search_exa,
    "parameters": {
        "query": "string",
    }
}

# Analysis tools
market_details_tool = {
    "name": "get_market_details",
    "description": (
        "Get detailed market information including prices, status, and metrics. "
        "Provide a market_id to get details."
    ),
    "func": get_market_details,
    "parameters": {
        "market_id": "string",
    }
}

orderbook_analysis_tool = {
    "name": "get_orderbook_analysis",
    "description": (
        "Analyze the orderbook for depth, liquidity, and pricing. "
        "Provide a token_id to analyze."
    ),
    "func": get_orderbook_analysis,
    "parameters": {
        "token_id": "string",
    }
}

# Trade tool
trade_tool = {
    "name": "trade",
    "description": (
        "Finalize your trade decision. Must provide arguments: "
        "`side` (string: 'BUY YES' | 'SELL' | 'HOLD'), "
        "`reason` (string summary of your logic), "
        "`confidence` (float, 0 <= c <= 1)."
    ),
    "func": trade,
    "parameters": {
        "side": "string",
        "reason": "string",
        "confidence": "number"
    }
}

# Export all tools
__all__ = [
    "search_tavily_tool",
    "search_exa_tool",
    "market_details_tool",
    "orderbook_analysis_tool",
    "trade_tool",
    "call_agent_with_tools",
]

async def call_agent_with_tools(
    state: State,
    config: Optional[RunnableConfig],
    tools: list,
    system_text: str,
) -> Dict[str, Any]:
    """
    A helper to run the LLM with the given 'tools' bound. We'll insert the
    raw market data + any prior messages into the conversation, plus
    a system prompt specialized for the sub-agent's role.
    """
    # Build a system message
    market_data_str = json.dumps(state.market_data or {}, indent=2)
    system_msg = SystemMessage(content=f"{system_text}\n\nMarket data:\n{market_data_str}")

    # Combine with conversation so far
    messages = [system_msg] + state.messages

    # Create the model
    raw_model = init_model(config)
    # Bind the specified tools
    model = raw_model.bind_tools(tools, tool_choice="any")

    # Call the model
    response = await model.ainvoke(messages)
    if not isinstance(response, AIMessage):
        response = AIMessage(content=str(response))

    # Save the new AIMessage in the conversation
    new_messages = [response]

    # Check if any tool calls were made
    tool_calls = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_calls = response.tool_calls
        
        # Handle each tool call
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            tool_call_id = tool_call.get("id")
            
            # Find the matching tool
            tool_func = None
            for tool in tools:
                if tool.get("name") == tool_name:
                    tool_func = tool.get("func")
                    break
            
            if tool_func:
                try:
                    # Execute the tool
                    tool_result = await tool_func(**tool_args, state=state, config=config)
                    # Add the tool response message
                    tool_message = ToolMessage(
                        tool_call_id=tool_call_id,
                        content=str(tool_result),
                        name=tool_name,
                        status="success"
                    )
                    new_messages.append(tool_message)
                except Exception as e:
                    # Add error message for failed tool calls
                    tool_message = ToolMessage(
                        tool_call_id=tool_call_id,
                        content=f"Error: {str(e)}",
                        name=tool_name,
                        status="error"
                    )
                    new_messages.append(tool_message)

    # If a trade call was made, store that in state
    for tool_call in tool_calls:
        if tool_call.get("name") == "Trade":
            trade_submitted = tool_call.get("args")
            side = trade_submitted.get("side")
            confidence = float(trade_submitted.get("confidence", 0))
            state.trade_decision = side
            state.confidence = confidence

    return {
        "messages": new_messages,
        "proceed": True,
        "loop_step": state.loop_step + 1,
    }