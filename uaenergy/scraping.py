"""
Functions for scraping content from the website.
"""

import os
import re
from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime
from random import shuffle
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from tqdm import tqdm

__all__ = ["WEBSITE", "parse_news"]

WEBSITE = "https://ua-energy.org"


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
    text: str | None = None
    tags: list[str] | None = None
    hrefs: list[str] | None = None

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
            url = urljoin(WEBSITE, metadata.url)
        else:
            url = metadata.url

        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, features="html.parser")
        article_div = soup.find("div", {"class": "content-article-inner"})
        if article_div is None:
            return cls(url=url, title=metadata.title, time=metadata.time)
        pattern = re.compile(urljoin(WEBSITE, "uk/posts"))
        hrefs = [tag.get("href") for tag in article_div.find_all("a", href=pattern)]
        paragraphs = [
            tag.text
            for tag in article_div.find_all("p")
            if not "ЧИТАЙТЕ ТАКОЖ" in tag.text
        ]
        tags = article_div.find("div", {"class": "tags"})
        if tags is not None:
            tags = {tag.get("href"): tag.text for tag in tags.find_all("a")}

        return cls(
            url=url,
            text=" ".join(paragraphs),
            tags=tags,
            hrefs=hrefs or None,
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
    response = requests.get(urljoin(WEBSITE, "uk/news"), params={"date": date})
    response.raise_for_status()

    # locating news section and parsing the articles
    soup = BeautifulSoup(response.content, features="html.parser")
    news_block = soup.find("h1", {"class": "title"}).next_sibling
    articles = news_block.find_all("div", {"class": "article"})
    metadata_list = list(map(Metadata.from_tag, articles))
    df = pd.DataFrame([Article.from_metadata(metadata) for metadata in metadata_list])
    return df


if __name__ == "__main__":

    # define the CLI
    parser = ArgumentParser(description="An addition program")
    parser.add_argument(
        "-s",
        "--start",
        default="21-12-2020",
        type=str,
        help="The date to start scraping from in the format 'DD-MM-YYYY'.",
    )
    parser.add_argument(
        "-e",
        "--end",
        default=datetime.today().strftime("%d-%m-%Y"),
        type=str,
        help="The date to scrape to in the format 'DD-MM-YYYY'.",
    )
    parser.add_argument(
        "-p",
        "--path",
        default=os.curdir,
        type=str,
        help="Folder path to save the file to.",
    )
    parser.add_argument(
        "-r",
        "--random",
        action="store_true",
        help="Randomise the date order while scraping.",
    )
    args = parser.parse_args()

    # ensure the path exist
    if not os.path.exists(args.path):
        raise FileNotFoundError(f"{args.path} directory does not exist")
    file_path = os.path.join(args.path, f"ua-energy-news-{args.start}-{args.end}.jsonl")

    # create and shuffle dates if needed
    dates = pd.date_range(args.start, args.end, freq="D").strftime("%d-%m-%Y").tolist()
    if args.random:
        shuffle(dates)

    # scrape the news and save the dataset
    data = []
    for date in tqdm(dates):
        data.append(parse_news(date))
    df = pd.concat(data, axis=0, ignore_index=True)
    df.sort_values("time", ascending=True, ignore_index=True, inplace=True)
    df.to_json(file_path, orient="records", lines=True)
    print(f"Saved {len(df)} articles to {file_path}.")
