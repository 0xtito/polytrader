# <ai_context>
# This file defines external research tools for the Polymarket AI agent,
# such as TavilySearch, Exa, or web scraping. The agent can call these
# tools via LangChain or directly in the node functions in graph.py.
# </ai_context>

"""Utility functions for external research tools used by the Polymarket AI agent."""
from typing import Any, List

from langchain_community.tools.tavily_search import TavilySearchResults

from langchain_exa import ExaSearchResults  

async def search_tavily(query: str, max_results: int = 10) -> List[dict[str, Any]]:
    """Perform a simple Tavily search."""
    tavily = TavilySearchResults(max_results=max_results)
    results = await tavily.arun(query)
    print("Tavily results: ", results)
    return results

def search_exa(query: str, max_results: int = 10) -> List[dict[str, Any]]:
    """Perform a simple Exa search."""
    print("Instantiating ExaSearchResults")
    exa = ExaSearchResults(max_results=max_results)
    print("Exa query: ", query)

    # create the invoke arg
    invoke_arg = {"query": query, "num_results": max_results}

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
    
    print("Exa results: ", structured_results)
    return structured_results


# async def scrape_website(url: str) -> str:
#     """Fetch HTML content for a given URL and return up to 50k characters with a timeout."""
#     try:
#         async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
#             async with session.get(url) as response:
#                 content = await response.text()
#                 return content[:50000]
#     except Exception as e:
#         print(f"Error scraping website {url}: {e}")  # T201 left in place
#         raise e


def structure_research(raw_text: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Structure the scraped research text into a given schema."""
    structured = dict(schema)  # copy
    structured["summary"] = raw_text[:200]
    structured["headline"] = "Sample Headline"
    structured["source_links"] = ["N/A"]
    return structured