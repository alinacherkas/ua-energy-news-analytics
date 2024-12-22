import pandas as pd
import requests
from bs4 import BeautifulSoup


def parse_article(article):
    """
    Parse article preview on newspage to extract title, link and time

    Parameters
    ----------
    article : bs4.tag
        article tag to be parsed

    Returns
    -------
    title, link, time : Tuple
        a tuple containing title, link and time of the article
    """

    title = article.a.text
    link = article.a.get("href")
    time = " ".join([x.text for x in article.find_all("span")])

    return title, link, time


def parse_news(link: str, use_date: bool = True):
    """
    Parses all articles on a newspage for a given date to produce a structured dataframe. Uses parse_articles.

    Parameters
    ----------
    link : str
        a full link to a newspage to be parsed or a date ('%d-%m-%Y') if use_date is True
    use_date : bool
        a flag indicating whether the provided link is a full link or just a date

    Returns
    -------
    df_articles: pd.DataFrame
        a dataframe of parsed articles with key information
    """
    if use_date:
        link = f"https://ua-energy.org/uk/news?date={link}"

    # Obtaining .html page and checking the status code
    results = requests.get(link)
    assert results.status_code == 200, f"HTTP Error Code: {results.status_code}"

    # Locating news section and parsing the articles
    soup = BeautifulSoup(results.content, features="html.parser")
    news_section = soup.find_all("div", {"class": "wrap"})[1]
    articles = news_section.find_all("div", {"class": "article"})
    df_articles = pd.DataFrame(
        [parse_article(x) for x in articles], columns=["Title", "Link", "Date"]
    )

    return df_articles


def get_article_content(link: str, add_root: bool = True, warnings: bool = False):
    """
    Parse a full article to extract basic information

    Parameters
    ----------
    link : str
        a link to a full article
    add_root : bool
        a flag whether to prefix the link with the root or not
    warnings : bool
        a flag whether to print a link if except clause is trigerred

    Returns
    -------
    link, article_text, tags, read_also : Tuple
        a tuple containing basic information from the article
    """
    if add_root:
        link = "https://ua-energy.org" + link

    results = requests.get(link)
    assert results.status_code == 200, f"HTTP Error Code: {results.status_code}"

    soup = BeautifulSoup(results.content, features="html.parser")
    class_name = "col-lg-7 col-md-8 col-sm-8 col-lg-offset-2 content-article content-article-inner"
    article_object = soup.find("div", {"class": class_name})
    if article_object is None:
        if warnings:
            print("No article found:", link)
        return link, None, None, None

    read_also = [
        tag.a.get("href")
        for tag in article_object.find_all("p")
        if "ЧИТАЙТЕ ТАКОЖ" in tag.text and tag.find("a") is not None
    ]
    if len(read_also) == 0:
        read_also = None

    article_text = [
        tag.text
        for tag in article_object.find_all("p")
        if not "ЧИТАЙТЕ ТАКОЖ" in tag.text
    ]
    article_text = " ".join(article_text)

    try:
        tags = article_object.find("div", {"class": "tags"})
        tags = {tag.get("href"): tag.text for tag in tags.find_all("a")}
    except:
        if warnings:
            print("No tags found:", link)
        tags = None

    return link, article_text, tags, read_also


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
