# <ai_context>
# This file holds configuration parameters for the Polymarket AI agent system.
# </ai_context>

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Optional
from typing_extensions import Annotated

from langchain_core.runnables import RunnableConfig, ensure_config

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

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/o3-mini",
        metadata={
            "description": "The name of the language model to use for the agent. "
            "Should be in the form: provider/model-name."
        },
    )

    temperature: float = field(
        default=0.5,
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

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        """Load configuration w/ defaults for the given invocation."""
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})
