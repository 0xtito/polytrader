# <ai_context>
# This file holds configuration parameters for the Polymarket AI agent system.
# </ai_context>

from __future__ import annotations

import os
from dotenv import load_dotenv
from dataclasses import dataclass, field, fields
from typing import Optional
from typing_extensions import Annotated

from langchain_core.runnables import RunnableConfig, ensure_config

from polytrader import prompts

load_dotenv()

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

    research_agent_prompt: str = field(
        default=prompts.RESEARCH_AGENT_PROMPT,
        metadata={
            "description": "The main prompt template to use for the research sub-agent. "
            "Expects f-string arguments like {info}, {market_data}, {question}, {description}, {outcomes}."
        },
    )

    # Added for the analysis sub-agent
    analysis_agent_prompt: str = field(
        default=prompts.ANALYSIS_AGENT_PROMPT,
        metadata={
            "description": "The prompt template for the analysis sub-agent."
        },
    )

    # Added for the trade sub-agent
    trade_agent_prompt: str = field(
        default=prompts.TRADE_AGENT_PROMPT,
        metadata={
            "description": "The prompt template for the trade sub-agent."
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

    firecrawl_api_key: str = field(
        default=os.getenv("FIRECRAWL_API_KEY"),
        metadata={
            "description": "The API key for the Firecrawl search engine."
        },
    )

    firecrawl_api_url: str = field(
        default="https://api.firecrawl.com",
        metadata={
            "description": "The API URL for the Firecrawl search engine."
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