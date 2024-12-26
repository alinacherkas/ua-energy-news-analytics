"""
Functions for scraping content from [UA-Energy.org](https://ua-energy.org).
"""

from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag


@dataclass
class Metadata:
    url: str
    title: str
    time: str

    @classmethod
    def from_tag(cls, tag: Tag) -> "Metadata":
        """
        Factory method to create an article metadata from an HTML tag.

        Parameters
        ----------
        tag : Tag
            HTML tag of the article.
        """
        date_str = " ".join([x.text for x in tag.find_all("span")])
        return cls(
            url=tag.a.get("href"),
            title=tag.a.text,
            time=cls.standardise_date(date_str),
        )

    @staticmethod
    def standardise_date(date: str) -> str:
        """
        Standardise an original date string into an ISO format.

        Parameters
        ----------
        date : str
            Publication date in Ukrainian.

        Returns
        -------
        str
            Date in ISO 8601 format (UTC+2).
        """
        months = {
            "січня": "January",
            "лютого": "February",
            "березня": "March",
            "квітня": "April",
            "травня": "May",
            "червня": "June",
            "липня": "July",
            "серпня": "August",
            "вересня": "September",
            "жовтня": "October",
            "листопада": "November",
            "грудня": "December",
        }
        for month_ua, month_en in months.items():
            if month_ua in date:
                date = date.replace(month_ua, month_en)
                date = datetime.strptime(date, "%d %B %Y, %H:%M")
                return date.isoformat()
        raise ValueError(f"Did not find a match for {date}")


@dataclass
class Article(Metadata):
    text: str
    tags: list[str]
    similar: list[str]

    @classmethod
    def from_metadata(cls, metadata: Metadata) -> "Article":
        """
        Parse a full article to extract basic information

        Parameters
        ----------
        metadata : Metadata
            Article metadata object.
        """
        if not metadata.url.startswith("https"):
            url = "https://ua-energy.org" + metadata.url
        else:
            url = metadata.url

        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, features="html.parser")
        article_object = soup.find("div", {"class": "content-article-inner"})
        if article_object is None:
            return cls(
                url=url,
                text=None,
                tags=None,
                similar=None,
                title=metadata.title,
                time=metadata.time,
            )

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

        return cls(
            url=url,
            text=text,
            tags=tags,
            similar=similar,
            title=metadata.title,
            time=metadata.time,
        )


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
    metadata_list = list(map(Metadata.from_tag, articles))
    df = pd.DataFrame([Article.from_metadata(metadata) for metadata in metadata_list])
    return df
