# <ai_context>
# This file defines external research tools for the Polymarket AI agent,
# such as TavilySearch, Exa, or web scraping. The agent can call these
# tools via LangChain or directly in the node functions in graph.py.
# </ai_context>

"""Utility functions for external research tools used by the Polymarket AI agent."""
import aiohttp
from typing import Any, List

from langchain_community.tools.tavily_search import TavilySearchResults


async def search_tavily(query: str, max_results: int = 10) -> List[dict[str, Any]]:
    """Perform a simple Tavily search."""
    tavily = TavilySearchResults(max_results=max_results)
    results = await tavily.arun(query)
    return results


async def scrape_website(url: str) -> str:
    """Fetch HTML content for a given URL and return up to 50k characters."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            return content[:50000]


def structure_research(raw_text: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Structure the scraped research text into a given schema."""
    structured = dict(schema)  # copy
    structured["summary"] = raw_text[:200]
    structured["headline"] = "Sample Headline"
    structured["source_links"] = ["N/A"]
    return structured