"""
Module for interacting with OpenAI to analyse energy news.
"""

import json
from importlib.resources import files

import yaml
from openai import OpenAI
from pydantic import BaseModel, Field

from .items import Topic

__all__ = ["ask_gpt", "select_topic", "translate_topics", "translate_tags"]


with files("uaenergy").joinpath("prompts.yaml").open() as file:
    PROMPTS = yaml.safe_load(file)


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
    completion = client.chat.completions.parse(
        messages=[
            {"role": "developer", "content": prompt},
            {"role": "user", "content": text},
        ],
        model="gpt-4o-mini",
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

    class TopicModel(BaseModel):
        """
        Topic model that represents the most coherent and relevant topics.
        """

        topic_names: list[str] = Field(
            description="Short and descriptive topic names in Ukrainian"
        )

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
    response = ask_gpt(message, PROMPTS["select_topic"], response_format=TopicModel)
    model = TopicModel.model_validate_json(response)
    return model.topic_names


def translate_topics(topics: list[str]) -> list[str]:
    """
    Translate a list of topics from Ukrainian to English.

    The function makes use of structured outputs. See
    https://platform.openai.com/docs/guides/structured-outputs

    Parameters
    ----------
    topics : list[str]
        A list of topics in Ukrainian.

    Returns
    -------
    list[str]
        A list of topics translated to English.
    """

    class TopicModel(BaseModel):
        """
        Topic model contains topics translated from Ukrainian into English.
        """

        topic_names: list[str] = Field(
            description="Short and descriptive topic names in English"
        )

    # construct an input message using Markdown
    message = json.dumps(topics, indent=2, ensure_ascii=False)
    response = ask_gpt(message, PROMPTS["translate_topics"], response_format=TopicModel)
    model = TopicModel.model_validate_json(response)
    return model.topic_names


def translate_tags(tags: list[str]) -> list[str]:
    """
    Translate a list of tags from Ukrainian to English.

    The function makes use of structured outputs. See
    https://platform.openai.com/docs/guides/structured-outputs

    Parameters
    ----------
    tags : list[str]
        A list of tags in Ukrainian.

    Returns
    -------
    list[str]
        A list of tags translated to English.
    """

    class Tags(BaseModel):
        """
        Tags object containing translated to English.
        """

        translated: list[str] = Field(description="Translated list of tags in English")

    # construct an input message using Markdown
    message = json.dumps(tags, indent=2, ensure_ascii=False)
    response = ask_gpt(message, PROMPTS["translate_tags"], response_format=Tags)
    model = Tags.model_validate_json(response)
    return model.translated
