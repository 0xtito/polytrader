# <ai_context>
# This file defines the dataclasses for the Polymarket agent's state,
# used by the LangGraph workflow.
# </ai_context>

"""Define states for Polymarket agent workflow."""
from dataclasses import dataclass, field
from typing import Annotated, Any, List, Optional, Dict, Union, Literal
from pydantic import BaseModel, Field, field_validator
from langchain.schema import BaseMessage
from langgraph.graph import add_messages


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

class Token(BaseModel):
    """A token in the market."""
    token_id: str
    """The token id of the token."""
    outcome: str
    """The outcome of the token."""

class TradeDecision(BaseModel):
    """Represents a trade decision for a binary market."""
    side: Literal["BUY", "SELL", "NO_TRADE"]
    """The side of the trade (BUY/SELL/NO_TRADE)."""
    outcome: Optional[str] = Field(
        None,
        description="The outcome to trade (YES/NO). Required for BUY/SELL, optional for NO_TRADE."
    )
    """The outcome to trade (YES/NO). Required for BUY/SELL, optional for NO_TRADE."""

    @field_validator('outcome')
    @classmethod
    def validate_outcome(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that outcome is present for BUY/SELL and is YES/NO."""
        side = info.data.get('side')
        if side in ["BUY", "SELL"]:
            if not v:
                raise ValueError("Outcome is required for BUY/SELL trades")
            if v not in ["YES", "NO"]:
                raise ValueError("Outcome must be either YES or NO")
        return v

    def __str__(self) -> str:
        """String representation of the trade decision."""
        if self.side == "NO_TRADE":
            return "NO_TRADE"
        return f"{self.side}_{self.outcome}"

@dataclass(kw_only=True)
class InputState:
    """Defines initial input to the graph."""

    market_id: str  # Changed from int to str to handle large numbers safely
    """The market id of the market."""
    custom_instructions: Optional[str] = None
    """Custom instructions for the agent."""
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

    debug: Optional[bool] = False
    """
    Whether the graph is being run in debug mode.
    """


@dataclass(kw_only=True)
class State(InputState):
    """The main mutable state during the graph's execution."""

    messages: Annotated[List[BaseMessage], add_messages] = field(default_factory=list)
    loop_step: int = 0
    market_data: Optional[dict[str, Any]] = None
    tokens: Optional[List[Token]] = None
    research_report: Optional[dict[str, Any]] = None
    trade_decision: Optional[TradeDecision] = None
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


class OrderResponse(BaseModel):
    """Represents the response from the order execution."""
    errorMsg: str
    """The error message from the order execution."""
    orderID: str
    """The order id from the order execution."""
    takingAmount: str
    """The amount of tokens taken from the order execution."""
    makingAmount: str
    """The amount of tokens made from the order execution."""
    status: str
    """The status of the order execution."""
    transactionsHashes: List[str]
    """The transactions hashes from the order execution."""

@dataclass(kw_only=True)
class OutputState:
    """This is the final output after the graph completes."""

    # research_report: ResearchResult
    research_report: dict[str, Any]
    analysis_info: dict[str, Any]
    trade_info: dict[str, Any]
    order_response: OrderResponse
    confidence: float