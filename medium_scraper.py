import csv
import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError, Timeout


BASE_FEED_URL = "https://medium.com/feed/tag/{tag}"


@dataclass(frozen=True)
class Article:
    title: str
    url: str
    content: str


def build_feed_url(tag: str) -> str:
    tag = (tag or "").strip().strip("/")
    if not tag:
        raise ValueError("tag is required (e.g. 'claude').")
    return BASE_FEED_URL.format(tag=tag)


def get_rss_links(feed_url: str, limit: int | None = None) -> list[dict[str, str]]:
    r = requests.get(feed_url, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.content, "xml")
    items = soup.find_all("item")

    articles: list[dict[str, str]] = []
    for item in items:
        title = (item.title.text or "").strip() if item.title else ""
        url = (item.link.text or "").strip() if item.link else ""
        if not title or not url:
            continue
        articles.append({"title": title, "url": url})

        if limit is not None and len(articles) >= limit:
            break

    return articles


def extract_article(url: str, *, max_retries: int = 3, timeout_s: int = 15) -> str | None:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(2 ** (attempt - 1))

            response = requests.get(url, headers=headers, timeout=timeout_s)
            response.raise_for_status()

            if "cf-challenge" in response.text or "Just a moment" in response.text:
                if attempt < max_retries - 1:
                    continue
                return None

            soup = BeautifulSoup(response.content, "html.parser")
            article = soup.find("article")
            if article:
                content = article.get_text()
            else:
                body = soup.find("body")
                content = body.get_text() if body else ""

            clean_content = "\n".join(
                line.strip() for line in content.splitlines() if line.strip()
            )
            return clean_content if len(clean_content) > 200 else None

        except (Timeout, ConnectionError):
            if attempt < max_retries - 1:
                continue
            return None
        except Exception:
            if attempt < max_retries - 1:
                continue
            return None

    return None


def scrape_medium_tag(
    tag: str,
    *,
    limit: int = 10,
    per_article_delay_s: float = 0.0,
    max_retries: int = 3,
) -> list[Article]:
    if limit <= 0:
        raise ValueError("limit must be >= 1")
    limit = min(int(limit), 50)

    feed_url = build_feed_url(tag)
    links = get_rss_links(feed_url, limit=limit)

    results: list[Article] = []
    for item in links:
        content = extract_article(item["url"], max_retries=max_retries)
        if content:
            results.append(Article(title=item["title"], url=item["url"], content=content))
        if per_article_delay_s > 0:
            time.sleep(per_article_delay_s)

    return results


def save_articles_csv(articles: list[Article], path: str) -> str:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "url", "content"])
        writer.writeheader()
        for a in articles:
            writer.writerow({"title": a.title, "url": a.url, "content": a.content})
    return path

