# <ai_context>
# This file defines the dataclasses for the Polymarket agent's state,
# used by the LangGraph workflow.
# </ai_context>

"""Define states for Polymarket agent workflow."""
from dataclasses import dataclass, field
from typing import Annotated, Any, List, Optional, Dict, Union

from langchain.schema import BaseMessage
from langgraph.graph import add_messages

from pydantic import BaseModel, Field


class ResearchResult(BaseModel):
    """A structured result of research."""
    report: str = Field(description="A detailed report of the research findings.")
    learnings: List[str] = Field(description="A list of key learnings from the research.")
    visited_urls: List[str] = Field(description="A list of URLs visited during the research.")

    # def model_dump(self) -> Dict[str, Any]:
    #     """Convert to a dictionary format."""
    #     return {
    #         "report": self.report,
    #         "learnings": self.learnings,
    #         "visited_urls": self.visited_urls
    #     }


@dataclass(kw_only=True)
class InputState:
    """Defines initial input to the graph."""

    market_id: str  # Changed from int to str to handle large numbers safely
    custom_instructions: Optional[str] = None
    extraction_schema: dict[str, Any] = field(
        default_factory=lambda: {"headline": "", "summary": "", "source_links": []}
    )
    """
    Tracks the current state of the external research fetched by the agent.
    Structure matches ResearchResult:
    {
        "report": str,  # Detailed research report
        "learnings": List[str],  # Key learnings from research
        "visited_urls": List[str]  # Sources visited during research
    }
    """

    # New fields for positions and funds
    positions: Optional[Dict[str, float]] = None
    """
    A dictionary representing the current user positions for each token_id in this market.
    e.g. positions = {"1234": 10.0} means user holds 10 units of token_id=1234
    If None or empty, the user has no positions in this market.
    """

    available_funds: float = 10.0
    """
    Amount of funds (USDC) the user has available to open new positions.
    Default is 10.0 if not provided.
    """

    from_js: Optional[bool] = False 
    """
    Whether the graph is being run from the web app using js.
    """


@dataclass(kw_only=True)
class State(InputState):
    """The main mutable state during the graph's execution."""

    messages: Annotated[List[BaseMessage], add_messages] = field(default_factory=list)
    loop_step: int = 0
    market_data: Optional[dict[str, Any]] = None
    research_report: Optional[dict[str, Any]] = None
    trade_decision: Optional[str] = None
    user_confirmation: Optional[bool] = None  # Track user confirmation for trades

    # Additional fields for storing agent outputs
    analysis_info: Optional[dict[str, Any]] = None
    trade_info: Optional[dict[str, Any]] = None
    confidence: Optional[float] = None

    # Fields for storing analysis tool data
    market_details: Optional[dict[str, Any]] = None
    orderbook_data: Optional[dict[str, Any]] = None
    market_trades: Optional[dict[str, Any]] = None
    historical_trends: Optional[dict[str, Any]] = None

    # Field for storing summarized search results
    search_results_summary: Optional[dict[str, Any]] = field(default=None)
    """
    A summary of search results, containing only key findings rather than raw content.
    Structure:
    {
        "query": str,  # The search query that was used
        "timestamp": str,  # When the search was performed
        "key_findings": List[str],  # List of main points from the search
        "sources": List[str]  # List of source URLs
    }
    """


@dataclass(kw_only=True)
class OutputState:
    """This is the final output after the graph completes."""

    # research_report: ResearchResult
    research_report: dict[str, Any]
    analysis_info: dict[str, Any]
    trade_info: dict[str, Any]
    confidence: float