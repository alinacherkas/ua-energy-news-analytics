"""
Functions for scraping content from the website.
"""

import os
from datetime import datetime
from random import shuffle
from typing import Optional
from urllib.parse import urljoin

import click
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from .items import Article, Metadata, WEBSITE

__all__ = ["parse_news"]


def parse_news(
    date: str, session: Optional[requests.Session] = None
) -> Optional[pd.DataFrame]:
    """
    Parses all articles on a newspage for a given date.

    Parameters
    ----------
    date : str
        A date in the format DD-MM-YYYY.
    session : requests.Session, optional
        A `requests.Session` object to use for the request. If None, a
        new session will be created. Default is None.

    Returns
    -------
    pd.DataFrame | None
        a dataframe of article metadata or None if no news are published on that date.
    """

    # obtaining HTML page and checking the status code
    request_func = requests.get if session is None else session.get
    response = request_func(urljoin(WEBSITE, "uk/news"), params={"date": date})
    if response.status_code == 404:
        return None
    response.raise_for_status()

    # locating news section and parsing the articles
    soup = BeautifulSoup(response.content, features="html.parser")
    news_block = soup.find("h1", {"class": "title"}).next_sibling
    articles = news_block.find_all("div", {"class": "article"})
    metadata_list = list(map(Metadata.from_tag, articles))
    df = pd.DataFrame(
        [Article.from_metadata(metadata, session) for metadata in metadata_list]
    )
    return df


@click.command(help="A web-scraper for UA-Energy.org.")
@click.option(
    "-s",
    "--start",
    default="21-12-2020",
    type=str,
    help="The date to start scraping from in the format 'DD-MM-YYYY'.",
)
@click.option(
    "-e",
    "--end",
    default=datetime.today().strftime("%d-%m-%Y"),
    type=str,
    help="The date to scrape to in the format 'DD-MM-YYYY'.",
)
@click.option(
    "-p",
    "--path",
    default=os.curdir,
    type=str,
    help="Folder path to save the file to.",
)
@click.option(
    "-r",
    "--random",
    is_flag=True,
    help="Randomise the date order while scraping.",
)
def main(start, end, path, random):
    # ensure the path exist
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} directory does not exist")

    # create and shuffle dates if needed
    dates = pd.date_range(start, end, freq="D").strftime("%d-%m-%Y").tolist()
    if random:
        shuffle(dates)

    # scrape the news
    data = []
    session = requests.Session()
    for date in tqdm(dates):
        df = parse_news(date, session)
        if df is None:
            continue
        data.append(df)
    df = pd.concat(data, axis=0, ignore_index=True)
    df.sort_values("date", ascending=True, ignore_index=True, inplace=True)

    # save the dataset
    file_name = f"ua-energy-news-{start}-{end}-raw.parquet.brotli"
    file_path = os.path.join(path, file_name)
    df.to_parquet(file_path, engine="fastparquet", compression="brotli")
    click.echo(f"Saved {len(df)} articles to {file_path}.")


if __name__ == "__main__":
    main()
