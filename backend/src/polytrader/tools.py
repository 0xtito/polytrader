# <ai_context>
# This file defines external research tools for the Polymarket AI agent,
# such as TavilySearch, Exa, or web scraping. The agent can call these
# tools via LangChain or directly in the node functions in graph.py.
# </ai_context>

"""Tools for Polymarket trading agent.

This module contains functions that are directly exposed to the LLM as tools.
These tools can be used for tasks such as web searching, market research and making trade decisions.
"""

import json
import logging
from typing import Any, Optional, cast, Dict, List
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from langchain_exa import ExaSearchResults
from langchain.schema import SystemMessage, AIMessage
from langchain_core.messages import ToolMessage
from datetime import datetime
from firecrawl import FirecrawlApp

from polytrader.configuration import Configuration
from polytrader.state import ResearchResult, State, TradeDecision
from polytrader.gamma import GammaMarketClient
from polytrader.polymarket import Polymarket
from polytrader.utils import generate_serp_queries, init_model, process_serp_result, write_final_report

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
gamma_client = GammaMarketClient()
poly_client = Polymarket()

################################################################################
# Search Tools
################################################################################

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

async def search_exa(
    query: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[list[dict[str, Any]]]:
    """Perform an Exa search to find relevant articles and information."""
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
            "title": getattr(result, "title", ""),
            "url": getattr(result, "url", ""),
            "content": getattr(result, "content", ""),
            "score": getattr(result, "score", 0),
            "published_date": getattr(result, "published_date", None)
        }
        formatted_results.append(formatted_result)
        
    # Log search results
    logger.info(f"Found {len(formatted_results)} results from Exa")

    return cast(list[dict[str, Any]], formatted_results)

################################################################################
# Analysis Tools (function-based)
################################################################################

async def analysis_get_market_details(
    market_id: str,
    *,
    state: Annotated[State, InjectedState],
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Get detailed information about a specific market."""
    logger.info(f"Fetching market details for market_id={market_id}")
    
    market_data = gamma_client.get_market(market_id)
    
    # Extract key trading metrics
    trading_metrics = {
        "current_prices": {
            "last_trade_price": market_data.get("lastTradePrice"),
            "best_bid": market_data.get("bestBid"),
            "best_ask": market_data.get("bestAsk"),
            "spread": market_data.get("spread"),
        },
        "volume_metrics": {
            "total_volume": market_data.get("volume"),
            "volume_24h": market_data.get("volume24hr"),
            "volume_clob": market_data.get("volumeClob"),
        },
        "liquidity_metrics": {
            "liquidity": market_data.get("liquidity"),
            "liquidity_clob": market_data.get("liquidityClob"),
        },
        "market_parameters": {
            "min_tick_size": market_data.get("orderPriceMinTickSize"),
            "min_order_size": market_data.get("orderMinSize"),
            "rewards_min_size": market_data.get("rewardsMinSize"),
            "rewards_max_spread": market_data.get("rewardsMaxSpread"),
        },
        "price_changes": {
            "24h_change": market_data.get("oneDayPriceChange"),
        },
        "outcomes": {
            "options": json.loads(market_data.get("outcomes", "[]")),
            "prices": json.loads(market_data.get("outcomePrices", "[]")),
        }
    }

    # Store in state
    state.market_details = trading_metrics
    
    logger.info("Market details tool returning data.")
    return trading_metrics

async def analysis_get_multi_level_orderbook(
    token_ids: List[str],
    levels: int = 10,
    *,
    state: Annotated[State, InjectedState],
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """
    Analyze multi-level orderbook for all tokens in the market.
    """
    logger.info(f"\nAnalyzing orderbook for tokens, top {levels} levels.")
    
    try:
        if not token_ids:
            return {
                "error": "No token IDs provided",
                "token_ids": []
            }
            
        # Create params for batch orderbook request
        book_params = [poly_client.BookParams(token_id=tid, side="BUY") for tid in token_ids]
        
        # Get orderbooks for all tokens
        orderbooks = poly_client.get_orderbooks(book_params)

        print("ORDERBOOKS:\n\n")
        print("Length of orderbooks: ", len(orderbooks))
        
        # Get last trade prices
        last_trades = poly_client.get_last_trades_prices(book_params)
        
        # Process each orderbook
        result = {
            "token_ids": token_ids,
            "orderbooks": {},
            "market_stats": {}
        }
        
        for i, (token_id, orderbook) in enumerate(zip(token_ids, orderbooks)):
            # Process top N levels
            top_bids = []
            if orderbook.bids:
                top_bids = [{
                    "price": float(order.price) if order.price else 0,
                    "size": float(order.size) if order.size else 0
                } for order in orderbook.bids[:levels]]

            top_asks = []
            if orderbook.asks:
                top_asks = [{
                    "price": float(order.price) if order.price else 0,
                    "size": float(order.size) if order.size else 0
                } for order in orderbook.asks[:levels]]
            
            # Calculate key metrics
            best_bid = float(top_bids[0]["price"]) if top_bids else None
            best_ask = float(top_asks[0]["price"]) if top_asks else None
            mid_price = (best_bid + best_ask) / 2 if best_bid is not None and best_ask is not None else None
            
            bid_depth = sum(float(order["size"]) for order in top_bids)
            ask_depth = sum(float(order["size"]) for order in top_asks)
            
            # Store orderbook analysis
            result["orderbooks"][token_id] = {
                "top_bids": top_bids,
                "top_asks": top_asks,
                "depth": {
                    "bid_depth": bid_depth,
                    "ask_depth": ask_depth,
                    "total_depth": bid_depth + ask_depth
                }
            }
            
            # Store market stats
            result["market_stats"][token_id] = {
                "best_bid": best_bid,
                "best_ask": best_ask,
                "mid_price": mid_price,
                "spread": best_ask - best_bid if best_ask and best_bid else None,
                "last_trade": last_trades[i] if i < len(last_trades) else None,
                "is_liquid": (bid_depth + ask_depth) > 1000
            }
        
        # Store in state
        state.orderbook_data = result
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to analyze orderbooks: {e}")
        return {
            "error": f"Failed to analyze orderbooks: {str(e)}",
            "token_ids": token_ids
        }

async def analysis_get_market_trades(
    market_id: str,
    *,
    state: Annotated[State, InjectedState],
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """
    Get market trades and events to analyze trading activity.
    """
    try:
        # Get market trades events
        trades = poly_client.get_market_trades_events(market_id)
        
        # Get token IDs
        token_ids = json.loads(state.market_data.get("clobTokenIds", "[]")) if state.market_data else []

        # Get last trade prices for each token
        book_params = [poly_client.BookParams(token_id=tid) for tid in token_ids]
        last_trades = poly_client.get_last_trades_prices(book_params)
        
        # Process last trades into a more structured format
        processed_trades = {
            trade["token_id"]: {
                "price": float(trade["price"]),
                "side": trade["side"]
            } for trade in last_trades
        }
        
        result = {
            "market_id": market_id,
            "trades": trades,
            "last_trades": processed_trades,
            "trade_summary": {
                "total_trades": len(trades) if trades else 0,
            }
        }
        
        # Store in state
        state.market_trades = result
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting market trades: {e}")
        return {
            "error": str(e),
            "market_id": market_id,
            "trades": []
        }

async def analysis_get_historical_trends(
    market_id: str,
    *,
    state: Annotated[State, InjectedState],
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """
    Analyze historical trends by combining market data and news sentiment.
    Uses market question for context and combines multiple data sources.
    """
    logger.info(f"Analyzing historical trends for market_id={market_id}")
    
    try:
        # Get market question and other relevant data
        if not state.market_data:
            return {
                "error": "No market data available",
                "market_id": market_id,
                "historical_data": []
            }
            
        market_question = state.market_data.get("question", "")
        outcomes = json.loads(state.market_data.get("outcomes", "[]"))
        outcome_prices = json.loads(state.market_data.get("outcomePrices", "[]"))
        
        # Construct a more informative search query using market details
        query = f"News and analysis about: {market_question}"
        if outcomes:
            query += f" Possible outcomes: {', '.join(outcomes)}"
            
        # Get news sentiment from Exa
        search_results = await search_exa(query, config=config)
        
        # Get market trade history
        token_ids = json.loads(state.market_data.get("clobTokenIds", "[]"))
        trade_history = []
        price_history = []
        
        for token_id in token_ids:
            try:
                # Get last trade price
                last_trade = poly_client.get_last_trade_price(token_id)
                if last_trade:
                    price_history.append({
                        "token_id": token_id,
                        "last_price": float(last_trade["price"]),
                        "side": last_trade["side"]
                    })
                
                # Get market trades events
                trades = poly_client.get_market_trades_events(market_id)
                if trades:
                    trade_history.append({
                        "token_id": token_id,
                        "trades": trades
                    })
            except Exception as e:
                logger.error(f"Error getting trade history for token {token_id}: {e}")
        
        # Combine market data
        market_data = {
            "question": market_question,
            "outcomes": outcomes,
            "outcome_prices": outcome_prices,
            "price_history": price_history,
            "trade_history": trade_history
        }
        
        # Analyze sentiment from news results
        sentiment_analysis = []
        if search_results:
            for result in search_results:
                sentiment_analysis.append({
                    "title": result.get("title", ""),
                    "date": result.get("date", ""),
                    "snippet": result.get("snippet", ""),
                    "url": result.get("url", "")
                })
            
        result = {
            "market_id": market_id,
            "market_data": market_data,
            "news_sentiment": sentiment_analysis,
            "analysis_summary": {
                "total_news_articles": len(sentiment_analysis),
                "total_trades": sum(len(th.get("trades", [])) for th in trade_history),
                "current_prices": outcome_prices,
                "timestamp": datetime.now().isoformat()
            }
        }

        # Store in state
        state.historical_trends = result
            
        logger.info("Historical trends analysis completed.")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing historical trends: {e}")
        return {
            "error": str(e),
            "market_id": market_id,
            "historical_data": []
        }

async def analysis_get_external_news(
    market_id: str,
    *,
    state: Annotated[State, InjectedState],
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """
    Search for external news relevant to the given market ID.
    This might yield articles or mentions that can influence the market.
    """
    logger.info(f"Attempting to get external news for market_id={market_id}")
    query = f"News or coverage regarding Polymarket market ID {market_id}"
    try:
        search_results = await search_exa(query, config=config)
        logger.info("External news search completed.")
        return {
            "market_id": market_id,
            "external_news": search_results or [],
            "note": "Mock external news data from exa search."
        }
    except Exception as e:
        logger.error(f"Error fetching external news: {e}")
        return {
            "error": str(e),
            "market_id": market_id,
            "external_news": []
        }

################################################################################
# Trade Tool (function-based)
################################################################################

async def trade(
    side: str,
    reason: str,
    confidence: float,
    *,
    state: Annotated[State, InjectedState],
    config: Annotated[RunnableConfig, InjectedToolArg],
    market_id: Optional[str] = None,
    token_id: Optional[str] = None,
    size: Optional[float] = None,
    outcome: Optional[str] = None,
    trade_evaluation_of_market_data: Optional[str] = None
) -> Dict[str, Any]:
    """Finalize a trade decision or do nothing."""
    logger.info("\n=== Trade Decision Analysis ===")

    # Create TradeDecision object
    try:
        trade_decision_obj = TradeDecision(side=side, outcome=outcome)
    except ValueError as e:
        raise ValueError(f"Invalid trade decision: {str(e)}")

    # If side is NO_TRADE, do nothing but record the decision
    if side == "NO_TRADE":
        trade_decision = {
            "side": side,
            "confidence": confidence,
            "reason": reason,
            "market_id": market_id,
            "token_id": token_id,
            "outcome": outcome,
            "size": size if size is not None else 0,
            "trade_evaluation_of_market_data": trade_evaluation_of_market_data,
        }
        state.trade_decision = trade_decision_obj
        state.confidence = confidence
        state.trade_info = trade_decision
        logger.info("Decision: NO_TRADE. Doing nothing.")
        return trade_decision

    # If side is BUY or SELL, proceed with normal logic
    # Find the correct token based on the outcome
    if state.tokens:
        token = next((t for t in state.tokens if t.outcome == outcome), None)
        if token:
            token_id = token.token_id
        else:
            raise ValueError(f"No token found for outcome: {outcome}")
        
    available_funds = poly_client.get_usdc_balance()

    trade_decision = {
        "side": side,
        "confidence": confidence,
        "reason": reason,
        "trade_evaluation_of_market_data": trade_evaluation_of_market_data,
        "market_id": market_id,
        "token_id": token_id,
        "outcome": outcome,
        "size": size,
        "market_context": {
            "market_data": state.market_data,
            "analysis_info": state.analysis_info,
            "positions": state.positions,
            "available_funds": available_funds
        },
    }

    # Update state with the validated TradeDecision object
    state.trade_decision = trade_decision_obj
    state.confidence = confidence
    state.trade_info = trade_decision

    # Log decision
    logger.info(f"Trade Decision: {trade_decision_obj}")
    logger.info(f"Confidence: {confidence}")
    logger.info(f"Reasoning: {reason}")
    logger.info(f"Market ID: {market_id}, Token ID: {token_id}, Size: {size}")
    logger.info(f"Trade Evaluation of Market Data: {trade_evaluation_of_market_data}")

    return trade_decision

class GetTokenIdParam(BaseModel):
    condition_id: str
    side: str

async def get_token_id(
    params: GetTokenIdParam,
    *,
    state: Annotated[State, InjectedState],
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Get the token ID for the given market ID and side."""
    logger.info(f"Getting token ID for market_id={params.market_id}, side={params.side}")

    # Get the token ID
    token_id = await poly_client.get_market(params.condition_id, params.side)
    return token_id
################################################################################
# Utility for calling agent with tools (kept for reference, not always used)
################################################################################

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
            for t in tools:
                if getattr(t, "name", None) == tool_name or t.__name__ == tool_name:
                    tool_func = t
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
        if tool_call.get("name") == "trade":
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

################################################################################
# NEW: Deep Research Tool
################################################################################

async def deep_research(
    query: str,
    max_depth: int = 2,
    max_links: int = 3,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg],
    state: Annotated[State, InjectedState]
) -> Dict[str, Any]:
    """
    Perform iterative deep web research using Firecrawl to gather extensive info on the provided query.
    The LLM can refine or expand sub-queries. This tool returns a structured summary of findings.
    """
    print(f"Starting deep_research for query='{query}' with max_depth={max_depth}, max_links={max_links}")

    improvement_instructions  = None
    research_report = state.research_report

    if (state.messages and 
        len(state.messages) > 0 and 
        hasattr(state.messages[-1], 'additional_kwargs') and 
        state.messages[-1].additional_kwargs and 
        "improvement_instructions" in state.messages[-1].additional_kwargs):
        improvement_instructions = state.messages[-1].additional_kwargs["improvement_instructions"]

    if improvement_instructions:
        query = improvement_instructions
    elif research_report and "report" in research_report:
        query = research_report["report"]
    else:
        query = state.market_data.get("question", "")

    # Load configuration
    configuration = Configuration.from_runnable_config(config)


    print("CALLING RECURSIVE FUNCTION")

    async def _deep_research_recursive(
        current_query: str,
        breadth: int,
        depth: int,
        learnings: List[str] = [],
        visited_urls: List[str] = [],
        progress: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        if len(progress) == 0:
            progress = {
                "currentDepth": depth,
                "totalDepth": depth,
                "currentBreadth": breadth,
                "totalBreadth": breadth,
                "totalQueries": 0,
                "completedQueries": 0
            }

            
        # Generate SERP queries
        serp_queries = await generate_serp_queries(
            current_query,
            main_question=state.market_data.get("question", ""),
            num_queries=breadth,
            learnings=learnings,
            improvement_instructions=improvement_instructions,
            config=config
        )

        print("--- SERP QUERIES ---")
        print(serp_queries)
        print("--- END SERP QUERIES ---")
        
        progress["totalQueries"] = len(serp_queries.queries)
        progress["currentQuery"] = serp_queries.queries[0].query if serp_queries.queries else None

        all_results = []
        new_breadth = breadth
        for serp_query in serp_queries.queries:
            try:
                # Search using Exa
                search_result = await search_exa(serp_query.query, config=config)
                
                # Format Exa results to match expected structure
                formatted_result = {
                    "success": True,
                    "data": []
                }
                
                # Extract relevant data from Exa results
                if search_result:
                    for item in search_result:
                        formatted_result["data"].append({
                            "url": item.get("url", ""),
                            "title": item.get("title", ""),
                            "description": item.get("content", "")
                        })
            
                # Process results
                processed_results = await process_serp_result(
                    serp_query.query,
                    formatted_result,
                    num_follow_up_questions=new_breadth,
                    config=config
                )

                print("--- Processed Results: ---")
                print(processed_results)
                print("--- END Processed Results ---")
                
                # Collect URLs from the processed result
                new_urls = [item.get("url", "") for item in formatted_result["data"] if item.get("url")]
                new_breadth = max(1, breadth // 2)
                new_depth = depth - 1
                
                all_learnings = learnings + processed_results.learnings
                all_urls = visited_urls + new_urls
                
                if new_depth > 0:
                    print(f"Researching deeper, breadth: {new_breadth}, depth: {new_depth}")
                    
                    progress.update({
                        "currentDepth": new_depth,
                        "currentBreadth": new_breadth,
                        "completedQueries": progress["completedQueries"] + 1,
                        "currentQuery": serp_query.query
                    })
                    
                    next_query = f"""
                    Previous research goal: {serp_query.research_goal}
                    Follow-up research directions: {chr(10).join(processed_results.follow_up_questions)}
                    """.strip()
                    
                    result = await _deep_research_recursive(
                        next_query,
                        new_breadth,
                        new_depth,
                        all_learnings,
                        all_urls,
                        progress
                    )
                    all_results.append(result)
                else:
                    progress.update({
                        "currentDepth": 0,
                        "completedQueries": progress["completedQueries"] + 1,
                        "currentQuery": serp_query.query
                    })
                    all_results.append({
                        "learnings": all_learnings,
                        "visitedUrls": all_urls
                    })
                    
            except Exception as e:
                print(f"Error processing query {serp_query.query}: {str(e)}")
                print(f"Full error: {e.__class__.__name__}: {str(e)}")
                all_results.append({
                    "learnings": [],
                    "visitedUrls": []
                })
                
        # Combine all results
        combined_learnings = list(set([
            learning 
            for result in all_results 
            for learning in result.get("learnings", [])
        ]))
        combined_urls = list(set([
            url 
            for result in all_results 
            for url in result.get("visitedUrls", [])
        ]))
        
        return {
            "learnings": combined_learnings,
            "visitedUrls": combined_urls
        }
    
    # Start recursive research
    research_results = await _deep_research_recursive(
        query,
        max_links,
        max_depth,
        learnings=state.research_report.get("learnings", []) if state.research_report else [],
        visited_urls=state.research_report.get("visitedUrls", []) if state.research_report else [],
    )

    # print("--- RESEARCH RESULTS ---")
    # print(research_results)
    # print("--- END RESEARCH RESULTS ---")
    
    # Generate final report
    final_report = await write_final_report(
        query,
        research_results["learnings"],
        research_results["visitedUrls"],
        config=config
    )

    print("--- FINAL REPORT ---")
    print(final_report)
    print("--- END FINAL REPORT ---")

    # Store in state using the ResearchResult model
    research_result = ResearchResult(
        report=final_report.report,
        learnings=research_results["learnings"],
        visited_urls=research_results["visitedUrls"]
    )
    
    return research_result.model_dump_json()
