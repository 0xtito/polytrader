# <ai_context>
# This file defines the dataclasses for the Polymarket agent's state,
# used by the LangGraph workflow.
# </ai_context>

"""Define states for Polymarket agent workflow."""
from dataclasses import dataclass, field
from typing import Annotated, Any, List, Optional, Dict, Union

from langchain.schema import BaseMessage
from langgraph.graph import add_messages


@dataclass(kw_only=True)
class InputState:
    """Defines initial input to the graph."""

    market_id: str  # Changed from int to str to handle large numbers safely
    custom_instructions: Optional[str] = None
    extraction_schema: dict[str, Any] = field(
        default_factory=lambda: {"headline": "", "summary": "", "source_links": []}
    )
    external_research_info: Optional[dict[str, Any]] = field(default=None)
    """
    Tracks the current state of the external research fetched by the agent.
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


@dataclass(kw_only=True)
class State(InputState):
    """The main mutable state during the graph's execution."""

    messages: Annotated[List[BaseMessage], add_messages] = field(default_factory=list)
    loop_step: int = 0
    market_data: Optional[dict[str, Any]] = None
    external_research: Optional[dict[str, Any]] = None
    trade_decision: Optional[str] = None

    # Additional fields for storing agent outputs
    analysis_info: Optional[dict[str, Any]] = None
    trade_info: Optional[dict[str, Any]] = None
    confidence: Optional[float] = None

    # Fields for storing analysis tool data
    market_details: Optional[dict[str, Any]] = None
    orderbook_data: Optional[dict[str, Any]] = None
    market_trades: Optional[dict[str, Any]] = None
    historical_trends: Optional[dict[str, Any]] = None


@dataclass(kw_only=True)
class OutputState:
    """This is the final output after the graph completes."""

    external_research_info: dict[str, Any]
    analysis_info: dict[str, Any]
    trade_info: dict[str, Any]
    confidence: float