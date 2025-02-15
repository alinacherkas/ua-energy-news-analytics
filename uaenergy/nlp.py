"""
Functions for running natural language processing on website articles.
"""

import os
from dataclasses import asdict
from pprint import pprint
from typing import Optional

import click
import numpy as np
import pandas as pd
import requests
import uk_core_news_sm
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import Pipeline
from spacy.tokens import Doc
from tqdm import tqdm

from .items import NamedEntity, Topic
from .openai import select_topic

__all__ = [
    "extract_entities",
    "get_stopwords",
    "lemmatise",
    "fit_lda",
    "extract_topics",
]


def extract_entities(doc: Doc, context_size: int = 2) -> list[NamedEntity]:
    """
    Extract named entities from a document.

    Parameters
    ----------
    doc : Doc
        SpaCy document object.
    context_size: int
        Number of sentences before and after the entity to include as a context.

    Returns
    -------
    list[NamedEntity]
        List of named entity objects with context.
    """
    entities = []
    # token indices that denote the start and end of each sentence
    indices = [(sentence.start, sentence.end) for sentence in doc.sents]
    for index, (start, end) in enumerate(indices):
        for entity in doc[start:end].ents:
            if entity.label_ not in {"ORG", "PER", "LOC"}:
                continue
            index_start = max(index - context_size, 0)
            start, _ = indices[index_start]
            index_end = min(index + context_size, len(indices) - 1)
            _, end = indices[index_end]
            entity = NamedEntity(
                name=entity.text,
                lemma=entity.lemma_,
                label=entity.label_,
                context=[sent.text for sent in doc[start:end].sents],
            )
            entities.append(entity)
    return entities


def get_stopwords() -> list[str]:
    """
    Get a list of Ukrainian stopwords.

    The list is based on https://github.com/skupriienko/Ukrainian-Stopwords
    and includes energy-specific stopwords.

    Returns
    -------
    list[str]
        List of Ukrainian stopwords.
    """
    url = "https://raw.githubusercontent.com/skupriienko/Ukrainian-Stopwords/refs/heads/master/stopwords_ua.txt"
    response = requests.get(url)
    response.raise_for_status()
    stopwords = response.text.split("\n")
    stopwords.extend(
        [
            "год",
            "година",
            "грн",
            "куб",
            "кубометр",
            "мвт",
            "млн",
            "млрд",
            "рок",
            "тис",
            "тисяча",
            "тонна",
            "і",
            "іі",
            "ііі",
        ]
    )
    return stopwords


def lemmatise(doc: Doc) -> str:
    """
    Lemmatise a SpaCy document and remove tokens that contain non-alphabetic characters.

    Parameters
    ----------
    doc : Doc
        SpaCy document object.

    Returns
    -------
    str
        Lemmatised tokens joined by a white space.
    """
    return " ".join([token.lemma_ for token in doc if token.is_alpha])


def fit_lda(
    texts: list[str], n_topics: int, stopwords: Optional[list[str]] = None, **kwargs
) -> Pipeline:
    """
    Fit a Latent Dirichlet Allocation model on texts.

    The texts are vectorised using CountVectoriser.

    Parameters
    ----------
    texts : list[str]
        List of texts to be modelled.
    n_topics : int
        Desired number of topics.
    stopwords : list[str], optional
        Optional list of stopwords.
    **kwargs
        Extra arguments to pass to `LatentDirichletAllocation`.

    Returns
    -------
    Pipeline
        A fitted sklearn Pipeline object containing 'vectoriser' and 'lda' steps.
    """
    vectoriser = CountVectorizer(
        lowercase=True,
        stop_words=stopwords,
        ngram_range=(1, 2),
        min_df=5,
        max_features=30_000,
    )
    lda = LatentDirichletAllocation(
        n_components=n_topics,
        learning_method="batch",
        **kwargs,
        random_state=5,
    )
    pipe = Pipeline([("vectoriser", vectoriser), ("lda", lda)])
    pipe.fit(texts)
    return pipe


def extract_topics(pipe: Pipeline, n_features: int = 10) -> list[Topic]:
    """
    Extract topics and their top features from a topic modelling pipeline.

    Parameters
    ----------
    pipe : Pipeline
        A fitted sklearn Pipeline object containing 'vectoriser' and 'lda' steps.
    n_features : int
        Number of top features to extract for each topic.

    Returns
    -------
    list[Topic]
        Collection of topics.
    """
    df_components = pd.DataFrame(
        pipe.named_steps["lda"].components_,
        columns=pipe.named_steps["vectoriser"].get_feature_names_out(),
    )
    topics = []
    for index, row in df_components.iterrows():
        features = row.sort_values(ascending=False).head(n_features).index.to_list()
        topic = Topic(name=str(index), features=features)
        topics.append(topic)
    return topics


@click.command(help="An NLP pipeline for UA-Energy.org.")
@click.option(
    "-p",
    "--path",
    type=str,
    required=True,
    help="File path to scraped news.",
)
@click.option(
    "-n",
    "--n-topics",
    type=int,
    default=[5, 7, 10],
    multiple=True,
    help="Values for the number of topics to try.",
)
def main(path, n_topics):

    # ensure the path exist
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} file does not exist")
    elif not "-raw" in path:
        raise ValueError("The file name must contain '-raw'.")

    click.echo("Loading the model, stopwords and news data...")
    nlp = uk_core_news_sm.load()
    stopwords = get_stopwords()
    df = pd.read_parquet(path, engine="fastparquet").sample(1000)

    click.echo("Converting to docs...")
    docs = [doc for doc in tqdm(nlp.pipe(df["text"], batch_size=16))]
    texts = list(map(lemmatise, docs))
    click.echo("Extracting named entities...")
    df["entities"] = [list(map(asdict, extract_entities(doc))) for doc in tqdm(docs)]

    click.echo("Running topic models...")
    topics, pipes = {}, {}
    for n in tqdm(n_topics):
        pipe = fit_lda(texts, n_topics=n, stopwords=stopwords)
        topics[n] = extract_topics(pipe, n_features=25)
        pipes[n] = pipe
    # select the best topic model and assign topic names using OpenAI
    topic_names = np.array(select_topic(topics))
    n_topics = len(topic_names)
    topics, pipe = topics[n_topics], pipes[n_topics]
    click.echo("Selected the model with {n_topics} topics")
    for topic, name in zip(topics, topic_names):
        topic.name = name
    click.echo(pprint(topics))

    click.echo("Assigning topics...")
    df["topic"] = topic_names[pipe.transform(texts).argmax(axis=1)]

    click.echo("Removing infrequent tags...")
    tags_count = df["tags"].explode().value_counts()
    tags = set(tags_count[tags_count.gt(5)].index)
    df["tags"] = df["tags"].map(
        lambda values: (
            [value for value in values if value in tags] or None
            if values is not None
            else None
        )
    )

    path, name = os.path.split(path)
    file_path = os.path.join(path, name.replace("-raw", "-processed"))
    df.to_parquet(file_path, engine="fastparquet", compression="brotli")
    click.echo(f"Saved {len(df)} articles to {file_path}.")


if __name__ == "__main__":
    main()
