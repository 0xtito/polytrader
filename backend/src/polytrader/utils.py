"""Utility functions for the Polytrader."""
import ast
from datetime import datetime
import json
from typing import Any, Callable, Dict, List, Optional, cast

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from polytrader.configuration import Configuration


def parse_camel_case(key) -> str:
    """Convert a camelCase string to a spaced-out lower string."""
    output = ""
    for char in key:
        if char.isupper():
            output += " "
            output += char.lower()
        else:
            output += char
    return output


def preprocess_market_object(market_object: dict) -> dict:
    """Preprocess a market object by appending certain fields to its description."""
    description = market_object["description"]

    for k, v in market_object.items():
        if k == "description":
            continue
        if isinstance(v, bool):
            description += f" This market is{' not' if not v else ''} {parse_camel_case(k)}."
        if k in ["volume", "liquidity"]:
            description += f" This market has a current {k} of {v}."
    print("\n\ndescription:", description)  # T201 left
    market_object["description"] = description

    return market_object


def preprocess_local_json(file_path: str, preprocessor_function: Callable[[dict], dict]) -> None:
    """Preprocess a local JSON file using the provided preprocessor function."""
    with open(file_path, "r+") as open_file:
        data = json.load(open_file)

    output = []
    for obj in data:
        preprocessed_json = preprocessor_function(obj)
        output.append(preprocessed_json)

    split_path = file_path.split(".")
    new_file_path = split_path[0] + "_preprocessed." + split_path[1]
    with open(new_file_path, "w+") as output_file:
        json.dump(output, output_file)


def metadata_func(record: dict, metadata: dict) -> dict:
    """Merge record fields into metadata dictionary."""
    print("record:", record)  # T201 left
    print("meta:", metadata)   # T201 left
    for k, v in record.items():
        metadata[k] = v

    del metadata["description"]
    del metadata["events"]

    return metadata


def get_message_text(msg: AnyMessage) -> str:
    """Get the text content of a message."""
    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        return content.get("text", "")
    else:
        txts = [c if isinstance(c, str) else (c.get("text") or "") for c in content]
        return "".join(txts).strip()


def init_model(config: Optional[RunnableConfig] = None) -> BaseChatModel:
    """Initialize the configured chat model."""
    configuration = Configuration.from_runnable_config(config)
    fully_specified_name = configuration.model
    if "/" in fully_specified_name:
        provider, model = fully_specified_name.split("/", maxsplit=1)
    else:
        provider = None
        model = fully_specified_name
    return init_chat_model(model, model_provider=provider)

class FinalReport(BaseModel):
    """A final report on the research."""
    report: str = Field(description="The final report on the research.")
    learnings: List[str] = Field(description="A list of key learnings from the research.")
    visited_urls: List[str] = Field(description="A list of URLs visited during the research.")


async def write_final_report(
    prompt: str,
    learnings: List[str],
    visited_urls: List[str],
    *,
    config: RunnableConfig
) -> FinalReport:
    """Generate a final report based on all research learnings."""
    
    learnings_str = "\n".join([f"<learning>{learning}</learning>" for learning in learnings])
    if len(learnings_str) > 150000:
        learnings_str = learnings_str[:150000]
    
    raw_model = init_model(config)
    prompt = f"""Given the following prompt from the user, write a final report on the topic using the learnings from research. 
Make it as detailed as possible, aim for 3 or more pages, include ALL the learnings from research:

<prompt>{prompt}</prompt>

Here are all the learnings from previous research:

<learnings>
{learnings_str}
</learnings>"""
    
    model = raw_model.with_structured_output(FinalReport)

    response = cast(AIMessage, await model.ainvoke(prompt))
    

    return response

class SerpQuery(BaseModel):
    """A single SERP query with its research goal."""
    query: str = Field(description="The search query string")
    research_goal: str = Field(description="A detailed explanation of what we hope to learn from this query")

class GenerateSerpQueries(BaseModel):
    """Generate SERP queries for research based on user query and previous learnings."""
    queries: List[SerpQuery] = Field(description="A list of SERP queries to research the topic.")

async def generate_serp_queries(
    query: str,
    main_question: str,
    num_queries: int = 3,
    learnings: Optional[List[str]] = None,
    improvement_instructions: Optional[str] = None,
    *,
    config: RunnableConfig
) -> GenerateSerpQueries:
    """Generate SERP queries for research based on user query and previous learnings."""
    print(f"Generating SERP queries for: {query}")
    
    model = init_model(config).with_structured_output(GenerateSerpQueries)

    date = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""The current date is {date}. Given the following prompt from the user, generate a list of SERP queries to research the main research question.
Return a maximum of {num_queries} queries. Each query should have:
1. A search query string
2. A detailed explanation of what we hope to learn from this query

The research goal is to answer the question: <main_question>{main_question}</main_question>.

Make sure each query is unique and targets a different aspect of the research:

<prompt>{query}</prompt>

If applicable, there will be some additional feedback on what needs to be improved in the research:
<improvement_instructions>{improvement_instructions}</improvement_instructions>

{f'Here are some learnings from previous research, use them to generate more specific queries: {chr(10).join(learnings)}' if learnings else ''}
"""

    response = cast(GenerateSerpQueries, await model.ainvoke(prompt))
    
    return response

class ProcessedSerpResult(BaseModel):
    """Process search results to extract learnings and follow-up questions."""
    learnings: List[str] = Field(description="A list of key learnings from the search results.")
    follow_up_questions: List[str] = Field(description="A list of follow-up questions to research the topic.")

async def process_serp_result(
    query: str,
    result: Dict[str, Any],
    num_learnings: int = 3,
    num_follow_up_questions: int = 3,
    *,
    config: RunnableConfig
) -> ProcessedSerpResult:
    """Process search results to extract learnings and follow-up questions."""
    print(f"Processing SERP results for query: {query}")
    
    # Extract and format content from results
    contents = []
    if result.get("success") and result.get("data"):
        for item in result["data"]:
            content = f"""
Title: {item.get('title', '')}
URL: {item.get('url', '')}
Description: {item.get('description', '')}
            """.strip()
            contents.append(content)
    
    if not contents:
        return ProcessedSerpResult(learnings=[], follow_up_questions=[])
    
    model = init_model(config).with_structured_output(ProcessedSerpResult)
    prompt = f"""Given the following search results for the query <query>{query}</query>, 
generate two things:
1. A list of key learnings (maximum {num_learnings})
2. A list of follow-up questions (maximum {num_follow_up_questions})

Make each learning unique, information-dense, and be rich in content. Include specific details like:
- Names of people, places, companies
- Exact numbers, dates, statistics
- Key relationships or trends
- Specific claims or findings

Search Results:
{chr(10).join([f'<result>{content}</result>' for content in contents])}"""

    print("--- PROCESS SERP RESULT PROMPT ---")
    print(prompt)
    print("--- END PROCESS SERP RESULT PROMPT ---")

    response = cast(ProcessedSerpResult, await model.ainvoke(prompt))

    print("--- PROCESS SERP RESULT RESPONSE ---")
    print(response)
    print("--- END PROCESS SERP RESULT RESPONSE ---")

    return response

