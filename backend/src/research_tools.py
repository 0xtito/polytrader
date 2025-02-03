# <ai_context>
# This file demonstrates integration with external research APIs such as Tavily, Exa,
# or custom scrapers. In production, these methods would query real APIs and return
# relevant data for the AI agent to consider.
# </ai_context>

import aiohttp

class ResearchTools:
    def __init__(self, tavily_api_key="", exa_api_key=""):
        self.tavily_api_key = tavily_api_key
        self.exa_api_key = exa_api_key

    async def query_tavily(self, query: str):
        # Example usage
        # In reality, you'd call https://api.tavily.com/search with your key
        print(f"Querying Tavily for: {query}")
        # Return mock data
        return {"results": ["Mock result 1", "Mock result 2"]}

    async def query_exa(self, query: str):
        # Example usage
        print(f"Querying Exa for: {query}")
        # Return mock data
        return {"documents": ["Mock doc 1", "Mock doc 2"]}

    async def combined_research(self, topic: str):
        # Potentially do both Tavily and Exa and combine
        tavily_res = await self.query_tavily(topic)
        exa_res = await self.query_exa(topic)
        # Combine logic
        return {
            "topic": topic,
            "tavily_results": tavily_res,
            "exa_results": exa_res
        } 