# <ai_context>
# This file holds configuration parameters for the Polymarket AI agent system.
# </ai_context>

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Optional

"""
This configuration pattern is inspired by typical dataclass-based agent settings.
Users can adjust these parameters at runtime or in environment variables.
"""


@dataclass(kw_only=True)
class Configuration:
    """
    General configuration for the Polymarket agent.
    Extend or customize as needed.
    """

    model: str = field(
        default="gpt-4",
        metadata={
            "description": "The name of the language model to use for the agent. Example: openai/gpt-4"
        },
    )

    temperature: float = field(
        default=0.0,
        metadata={
            "description": "Temperature for the LLM; controls randomness in output."
        },
    )

    max_search_results: int = field(
        default=10,
        metadata={
            "description": "Maximum number of search results to return for each search query."
        },
    )

    max_info_tool_calls: int = field(
        default=3,
        metadata={
            "description": "Maximum number of times an info retrieval tool can be called."
        },
    )

    max_loops: int = field(
        default=6,
        metadata={
            "description": "Maximum number of iteration loops allowed in the graph before termination."
        },
    )
