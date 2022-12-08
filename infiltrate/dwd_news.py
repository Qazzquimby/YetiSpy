"""Handles extracting events from """
import itertools

import infiltrate.browsers as browsers

ROOT_URL = "https://www.direwolfdigital.com/"
NEWS_URL = "https://news.direwolfdigital.com/"
ARTICLE_SELECTOR = "section.allNews > div > div > a"
LEAGUE_PACKS_SELECTOR = (
    "section.pageContent > div > div > div.col-md-8.content > h2 + p + ul > li"
)


def get_news_links():
    soup = browsers.get_soup_from_url(NEWS_URL)
    articles = soup.select(ARTICLE_SELECTOR)
    if not articles:
        raise ValueError("No articles found on news page. Probably blocking scraping")
    return articles


def _get_league_links():
    articles = get_news_links()
    return [article for article in articles if "league" in article.text.lower()]


def _get_most_recent_league_link():
    articles = _get_league_links()
    try:
        return articles[0]
    except IndexError:
        raise IndexError(
            "No league articles in recent news. "
            "Add support to checking the archives."
        )


def get_most_recent_league_article_url():
    link = _get_most_recent_league_link()
    url = f"{ROOT_URL}{link['href']}"
    return url


def get_most_recent_league_article_packs_text():
    url = get_most_recent_league_article_url()
    rows = browsers.get_texts_from_url_and_selector(url, LEAGUE_PACKS_SELECTOR)
    pack_texts = list(itertools.chain(*[row.split(",") for row in rows]))
    pack_texts = [pack_text.replace("\xa0", " ") for pack_text in pack_texts]
    return pack_texts
