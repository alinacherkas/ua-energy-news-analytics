"""
Functions for scraping content from [UA-Energy.org](https://ua-energy.org).
"""

from dataclasses import dataclass

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag


@dataclass
class ArticleMetadata:
    url: str
    title: str
    time: str

    @classmethod
    def from_tag(cls, tag: Tag) -> "ArticleMetadata":
        """
        Factory method to create an article from an HTML tag.

        Parameters
        ----------
        tag : Tag
            HTML tag of the article.
        """
        return cls(
            url=tag.a.get("href"),
            title=tag.a.text,
            time=" ".join([x.text for x in tag.find_all("span")]),
        )


@dataclass
class ArticleContent:
    url: str
    text: str
    tags: list[str]
    similar: list[str]

    @classmethod
    def from_url(cls, url: str) -> "ArticleContent":
        """
        Parse a full article to extract basic information

        Parameters
        ----------
        url : str
            A URL to a full article.
        """
        if not url.startswith("https"):
            url = "https://ua-energy.org" + url

        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, features="html.parser")
        article_object = soup.find("div", {"class": "content-article-inner"})
        if article_object is None:
            return cls(url=url, text=None, tags=None, similar=None)

        similar = [
            tag.a.get("href")
            for tag in article_object.find_all("p")
            if "ЧИТАЙТЕ ТАКОЖ" in tag.text and tag.find("a") is not None
        ]
        if len(similar) == 0:
            similar = None

        text = " ".join(
            [
                tag.text
                for tag in article_object.find_all("p")
                if not "ЧИТАЙТЕ ТАКОЖ" in tag.text
            ]
        )

        try:
            tags = article_object.find("div", {"class": "tags"})
            tags = {tag.get("href"): tag.text for tag in tags.find_all("a")}
        except:
            tags = None

        return cls(url=url, text=text, tags=tags, similar=similar)


def parse_news(date: str) -> pd.DataFrame:
    """
    Parses all articles on a newspage for a given date.

    Parameters
    ----------
    date : str
        A date in the format DD-MM-YYYY.

    Returns
    -------
    df: pd.DataFrame
        a dataframe of article metadata.
    """

    # obtaining HTML page and checking the status code
    response = requests.get(f"https://ua-energy.org/uk/news?date={date}")
    response.raise_for_status()

    # locating news section and parsing the articles
    soup = BeautifulSoup(response.content, features="html.parser")
    news_section = soup.find_all("div", {"class": "wrap"})[1]
    articles = news_section.find_all("div", {"class": "article"})
    df = pd.DataFrame(map(ArticleMetadata.from_tag, articles))
    df = pd.DataFrame([ArticleContent.from_url(url) for url in df["url"]])
    return df


def replace_months(date: str):
    """
    Convert an original date string to a datetime object

    Parameters
    ----------
    date : str
        article tag to be parsed

    Returns
    -------
    pd.to_datetime(date) : Timestamp
        pandas timestamp object
    """
    months = {
        "жовтня": "October",
        "травня": "May",
        "квітня": "April",
        "листопада": "November",
        "вересня": "September",
        "березня": "March",
        "серпня": "August",
        "грудня": "December",
        "липня": "July",
        "лютого": "February",
        "червня": "June",
        "січня": "January",
    }

    ukr_month = date.split(" ")[1]
    date = date.replace(ukr_month, months[ukr_month])
    return pd.to_datetime(date)
