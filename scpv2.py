import time
import csv
import argparse
import requests
from bs4 import BeautifulSoup
from requests.exceptions import Timeout, ConnectionError


FEED_URL = "https://medium.com/feed/tag/claude"
DEFAULT_CSV_PATH = "medium_articles.csv"


def get_rss_links(feed_url):
    """Fetch RSS feed and extract article URLs"""
    r = requests.get(feed_url, timeout=20)
    soup = BeautifulSoup(r.content, "xml")

    articles = []
    for item in soup.find_all("item"):
        articles.append({
            "title": item.title.text.strip(),
            "url": item.link.text.strip()
        })

    return articles


def extract_article(url, max_retries=3):
    """Extract article content with retry logic and Cloudflare detection"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0"
    }

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                wait_time = 2 ** (attempt - 1)
                time.sleep(wait_time)

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            if "cf-challenge" in response.text or "Just a moment" in response.text:
                if attempt < max_retries - 1:
                    continue
                else:
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


def run_pipeline(feed_url):
    """Run scraping pipeline with Cloudflare handling"""
    articles = get_rss_links(feed_url)
    dataset = []

    print("\n" + "="*80)
    print("MEDIUM SCRAPER - Starting Pipeline")
    print("="*80 + "\n")

    for i, article in enumerate(articles, 1):
        print("[{:2d}/{}] Processing: {}...".format(i, len(articles), article['title'][:60]))

        content = extract_article(article["url"])

        if content:
            status = "[OK]"
            data_size = len(content)
            preview = content[:60].replace("\n", " ")
            dataset.append({
                "title": article["title"],
                "url": article["url"],
                "content": content
            })
        else:
            status = "[FAIL]"
            data_size = 0
            preview = "No content extracted"

        print("      {} Result: {:>6} chars | Preview: {}...".format(status, data_size, preview))
        time.sleep(4)

    print("\n" + "="*80)
    print("Pipeline Complete - Scraped {}/{}".format(len(dataset), len(articles)))
    print("="*80 + "\n")

    return dataset


def save_to_csv(dataset, path):
    fieldnames = ["title", "url", "content"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(dataset)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Medium RSS feed and save articles to CSV.")
    parser.add_argument("--feed-url", default=FEED_URL, help="Medium RSS feed URL")
    parser.add_argument("--out", default=DEFAULT_CSV_PATH, help="Output CSV path")
    args = parser.parse_args()

    data = run_pipeline(args.feed_url)
    if data:
        save_to_csv(data, args.out)
        print("[OK] Saved {} articles to {}".format(len(data), args.out))
        print("[OK] First Article: {}\n".format(data[0]['title']))
        print(data[0]["content"][:500])
    else:
        print("[FAIL] No articles extracted.")
