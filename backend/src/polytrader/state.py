# <ai_context>
# This file defines the dataclasses for the Polymarket agent's state,
# used by the LangGraph workflow.
# </ai_context>

"""Define states for Polymarket agent workflow."""
from dataclasses import dataclass, field
from typing import Annotated, Any, List, Optional

from langchain.schema import BaseMessage
from langgraph.graph import add_messages


@dataclass(kw_only=True)
class InputState:
    """Defines initial input to the graph."""

    market_id: int 
    custom_instructions: Optional[str] = None
    extraction_schema: dict[str, Any] = field(
        default_factory=lambda: {"headline": "", "summary": "", "source_links": []}
    )
    external_research_info: Optional[dict[str, Any]] = field(default=None)
    """
    Tracks the current state of the external research fetched by the agent.
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


@dataclass(kw_only=True)
class OutputState:
    """This is the final output after the graph completes."""

    external_research_info: dict[str, Any]