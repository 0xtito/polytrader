# <ai_context>
# This file demonstrates integration with external research APIs such as Tavily, Exa,
# or custom scrapers. In production, these methods would query real APIs and return
# relevant data for the AI agent to consider.
# </ai_context>

class ResearchTools:
    """Collection of research tools to query Tavily, Exa, or similar services."""

    def __init__(self, tavily_api_key="", exa_api_key=""):
        """Initialize the research tools with given API keys."""
        self.tavily_api_key = tavily_api_key
        self.exa_api_key = exa_api_key

    async def query_tavily(self, query: str):
        """Query Tavily with the provided query string."""
        print(f"Querying Tavily for: {query}")  # T201 left in place
        return {"results": ["Mock result 1", "Mock result 2"]}

    async def query_exa(self, query: str):
        """Query Exa with the provided query string."""
        print(f"Querying Exa for: {query}")  # T201 left in place
        return {"documents": ["Mock doc 1", "Mock doc 2"]}

    async def combined_research(self, topic: str):
        """Perform combined research using Tavily and Exa and return aggregated results."""
        tavily_res = await self.query_tavily(topic)
        exa_res = await self.query_exa(topic)
        return {"topic": topic, "tavily_results": tavily_res, "exa_results": exa_res}