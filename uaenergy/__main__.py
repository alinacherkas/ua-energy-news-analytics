"""
A CLI interface for the package.
"""

import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from pprint import pprint
from random import shuffle

import click
import numpy as np
import pandas as pd
import requests
import uk_core_news_sm

from .nlp import extract_entities, extract_topics, fit_lda, get_stopwords, lemmatise
from .openai import select_topic, translate_tags, translate_topics
from .scraping import parse_news


@click.group()
def cli():
    """
    A CLI for scraping and processing energy news from https://ua-energy.org.
    """
    pass


@cli.command(help="Web-scrape news articles from UA-Energy.org.")
@click.option(
    "--date-start",
    default="2020-12-21",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Scrape articles published since this date.",
)
@click.option(
    "--date-end",
    default=datetime.today(),
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Scrape articles published before this date.",
)
@click.option(
    "-p",
    "--path",
    default=os.curdir,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Folder path to save the file to.",
)
@click.option(
    "-r",
    "--random",
    is_flag=True,
    help="Randomise the date order while scraping.",
)
def scrape(date_start, date_end, path, random):
    # create and shuffle dates if needed
    dates = pd.date_range(date_start, date_end, freq="D").strftime("%d-%m-%Y").tolist()
    if random:
        shuffle(dates)

    # scrape the news
    data = []
    with requests.Session() as session:
        with click.progressbar(dates, label="Scraping articles...") as bar:
            for date in bar:
                bar.label = f"Scraping articles ({date})"
                df = parse_news(date, session)
                if df is None:
                    continue
                data.append(df)

    df = pd.concat(data, axis=0, ignore_index=True)
    df.sort_values("date", ascending=True, ignore_index=True, inplace=True)

    # save the dataset
    file_name = (
        f"ua-energy-news-{date_start:%Y-%m-%d}-{date_end:%Y-%m-%d}-raw.parquet.brotli"
    )
    file_path = path.joinpath(file_name)
    df.to_parquet(file_path, engine="fastparquet", compression="brotli")
    click.echo(f"Saved {len(df)} articles to {file_path}.")


@cli.command()
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
)
@click.option(
    "-n",
    "--n-topics",
    type=int,
    default=[5, 7, 10],
    multiple=True,
    help="Values for the number of topics to try.",
)
def process(path, n_topics):
    """
    Process scraped articles using an NLP pipeline.

    PATH: File path to scraped news.
    """
    if not "-raw" in path.name:
        raise ValueError("The file name must contain '-raw'.")

    click.echo("Loading the model, stopwords and news data...")
    nlp = uk_core_news_sm.load()
    stopwords = get_stopwords()
    df = pd.read_parquet(path, engine="fastparquet")

    pipe = nlp.pipe(df["text"], batch_size=16)
    with click.progressbar(pipe, length=len(df), label="Converting to docs") as bar:
        docs = [doc for doc in bar]
    with click.progressbar(docs, label="Extracting named entities") as bar:
        df["entities"] = [list(map(asdict, extract_entities(doc))) for doc in bar]

    texts = list(map(lemmatise, docs))
    topics, pipes = {}, {}
    with click.progressbar(n_topics, label="Running topic models") as bar:
        for n in bar:
            pipe = fit_lda(texts, n_topics=n, stopwords=stopwords)
            topics[n] = extract_topics(pipe, n_features=25)
            pipes[n] = pipe
    # select the best topic model and assign topic names using OpenAI
    topic_names = np.array(select_topic(topics))
    n_topics = len(topic_names)
    topics, pipe = topics[n_topics], pipes[n_topics]
    click.echo(f"Selected the model with {n_topics} topics")
    for topic, name in zip(topics, topic_names):
        topic.name = name
    click.echo(pprint(topics))

    click.echo("Assigning topics...")
    topics = [topic.name for topic in topics]
    mapping = dict(zip(topics, translate_topics(topics)))
    click.echo(pprint(mapping))
    df["topic_uk"] = topic_names[pipe.transform(texts).argmax(axis=1)]
    df["topic_en"] = df["topic_uk"].map(mapping)

    click.echo("Cleaning and translating tags...")
    tags_count = df["tags"].explode().value_counts()
    tags_uk = tags_count[tags_count.gt(5)].index.tolist()
    tags_en = translate_tags(tags_uk)
    if len(tags_uk) != len(tags_en):
        click.echo("Tags translation is likely incorrect, please try again.", err=True)
    tags_translations = dict(zip(tags_uk, tags_en))
    df["tags_uk"] = df["tags"].map(
        lambda tags: (
            [tag for tag in tags if tag in tags_translations] or None
            if tags is not None
            else None
        )
    )
    df["tags_en"] = df["tags_uk"].map(
        lambda tags: (
            [tags_translations[tag] for tag in tags] if tags is not None else None
        )
    )
    df.drop(columns=["tags"], inplace=True)

    click.echo("Saving data...")
    file_path = path.with_name(path.name.replace("-raw", "-processed"))
    df.to_parquet(file_path, engine="fastparquet", compression="brotli")
    click.echo(f"Saved {len(df)} articles to {file_path}.")


if __name__ == "__main__":
    cli()
