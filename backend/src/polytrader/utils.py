"""Utility functions for the Polytrader."""
import json
from typing import Callable

from typing import Optional

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig

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
    print("fully_specified_name:", fully_specified_name)
    if "/" in fully_specified_name:
        provider, model = fully_specified_name.split("/", maxsplit=1)
    else:
        provider = None
        model = fully_specified_name
    print("provider:", provider)
    print("model:", model)
    return init_chat_model(model, model_provider=provider)