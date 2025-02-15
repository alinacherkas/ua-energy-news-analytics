"""
Data items for storing object properties.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

__all__ = ["WEBSITE", "Metadata", "Article", "NamedEntity", "Topic"]

WEBSITE = "https://ua-energy.org"


@dataclass
class Metadata:
    """
    Article metadata.
    """

    url: str
    title: str
    date: datetime

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
            date=cls.standardise_date(date_str),
        )

    @staticmethod
    def standardise_date(date: str) -> datetime:
        """
        Standardise an original date string into a datatime object.

        Parameters
        ----------
        date : str
            Publication date in Ukrainian.

        Returns
        -------
        datetime
            Publication date as a datetime object (UTC+2).
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
                return date
        raise ValueError(f"Did not find a match for {date}")


@dataclass
class Article(Metadata):
    """
    News article, including metadata.
    """

    text: Optional[str] = None
    tags: Optional[list[str]] = None
    hrefs: Optional[list[str]] = None

    @classmethod
    def from_metadata(
        cls, metadata: Metadata, session: Optional[requests.Session] = None
    ) -> "Article":
        """
        Parse a full article to extract basic information

        Parameters
        ----------
        metadata : Metadata
            Article metadata object.
        session : requests.Session, optional
            A `requests.Session` object to use for the request. If None, a
            new session will be created. Default is None.
        """
        if not metadata.url.startswith("https"):
            url = urljoin(WEBSITE, metadata.url)
        else:
            url = metadata.url

        request_func = requests.get if session is None else session.get
        response = request_func(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, features="html.parser")
        article_div = soup.find("div", {"class": "content-article-inner"})
        if article_div is None:
            return cls(url=url, title=metadata.title, date=metadata.date)
        pattern = re.compile(urljoin(WEBSITE, "uk/posts"))
        hrefs = [tag.get("href") for tag in article_div.find_all("a", href=pattern)]
        paragraphs = [
            tag.text
            for tag in article_div.find_all("p")
            if not "ЧИТАЙТЕ ТАКОЖ" in tag.text
        ]
        tags = article_div.find("div", {"class": "tags"})
        if tags is not None:
            tags = [tag.text for tag in tags.find_all("a")]

        return cls(
            url=url,
            text=" ".join(paragraphs),
            tags=tags,
            hrefs=hrefs or None,
            title=metadata.title,
            date=metadata.date,
        )


@dataclass
class NamedEntity:
    """
    Named entity object with context.
    """

    name: str
    lemma: str
    label: str
    context: list[str]


@dataclass
class Topic:
    """
    News topic from a topic model.
    """

    name: str
    features: list[str]
