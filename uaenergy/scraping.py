"""
Functions for scraping content from the website.
"""

from typing import Optional
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .items import WEBSITE, Article, Metadata

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
