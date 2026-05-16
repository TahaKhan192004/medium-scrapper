from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from medium_scraper import save_articles_csv, scrape_medium_tag


mcp = FastMCP(
    "medium-scraper",
    dependencies=["requests", "beautifulsoup4", "lxml"],
)


@mcp.tool()
def fetch_medium_tag_articles(tag: str, limit: int = 10) -> list[dict[str, Any]]:
    """
    Fetch Medium articles for a tag via RSS and extract readable text.

    Args:
      tag: Medium tag slug (e.g. "claude" from https://medium.com/feed/tag/claude)
      limit: Max number of RSS items to attempt (1-50)

    Returns:
      List of {title, url, content}.
    """
    articles = scrape_medium_tag(tag, limit=limit, per_article_delay_s=1.0)
    return [{"title": a.title, "url": a.url, "content": a.content} for a in articles]


@mcp.tool()
def fetch_medium_tag_articles_to_csv(
    tag: str,
    limit: int = 10,
    csv_path: str = "medium_articles.csv",
) -> dict[str, Any]:
    """
    Fetch Medium tag articles and write them to a CSV file.

    Returns:
      {csv_path, scraped, requested}
    """
    articles = scrape_medium_tag(tag, limit=limit, per_article_delay_s=1.0)
    save_articles_csv(articles, csv_path)
    return {"csv_path": csv_path, "scraped": len(articles), "requested": min(int(limit), 50)}


if __name__ == "__main__":
    mcp.run()

