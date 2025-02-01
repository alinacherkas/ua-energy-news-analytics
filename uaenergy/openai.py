"""
Module for interacting with OpenAI to analyse energy news. 
"""

import json
from enum import StrEnum

from openai import OpenAI

from .nlp import Topic

__all__ = ["ask_gpt", "select_topic"]


class Prompts(StrEnum):
    """
    System prompts for OpenAI models.
    """

    SELECT_TOPIC = (
        "You are a natural language processing expert with a focus on news. "
        "You work on topic modelling of energy news in Ukraine, helping to choose among multiple models. "
        "Your task is two-fold. "
        "Firstly, select the topic model that produced the most coherent and relevant set of topics. "
        "Secondly, for each topic in that model, come up with a short and descriptive name in Ukrainian of no more than 5 words. "
        "Your inputs are models with a different number of topics. "
        "You must output a list of topic names for the model with the most coherent and relevant topics. "
        "The output must be an object containing topic names (that you come up with) with their corresponding topic features."
    )


def ask_gpt(text: str, prompt: str, **kwargs) -> str:
    """
    Ask a GPT model using `chat.completions.create` endpoint.

    The temperature is set to 0.0 and the seed is fixed.

    Parameters
    ----------
    text : str
        User input message.
    prompt : str
        System prompt to tune the model.
    **kwargs
        Extra arguments to pass to `chat.completions.create`.

    Returns
    -------
    str
        Response message content from the model.
    """
    client = OpenAI()
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": prompt},
            {"role": "user", "content": text},
        ],
        seed=5,
        temperature=0.0,
        **kwargs,
    )
    return completion.choices[0].message.content


def select_topic(model_topics: dict[int, list[Topic]]) -> list[str]:
    """
    Select the best topic model using a GPT model.

    The function makes use of structured outputs. See
    https://platform.openai.com/docs/guides/structured-outputs

    Parameters
    ----------
    model_topics : dict[int, list[Topic]]
        Mapping of model IDs to the list of topics.

    Returns
    -------
    list[str]
        A list of generated topic names for the model with
        the most coherent and relevant topics.
    """
    # define a JSON schema
    schema = {
        "properties": {
            "topic_names": {
                "description": "A list of short and descriptive topic names in Ukrainian",
                "items": {"type": "string"},
                "title": "Topic Names",
                "type": "array",
            }
        },
        "required": ["topic_names"],
        "title": "Output",
        "type": "object",
        "additionalProperties": False,
    }
    # use the schema to define the response format
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "topic_names_response",
            "schema": schema,
            "strict": True,
        },
    }
    # construct an input message using Markdown
    message = ""
    for model, topics in model_topics.items():
        message += f"\n### Topic Model {model}\n\n"
        topics = json.dumps(
            {topic.name: topic.features for topic in topics},
            indent=2,
            ensure_ascii=False,
        )
        message += f"```json\n{topics}\n```\n"
    response = ask_gpt(message, Prompts.SELECT_TOPIC, response_format=response_format)
    response = json.loads(response)
    return response["topic_names"]
