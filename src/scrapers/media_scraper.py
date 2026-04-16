"""Web scraper for traditional media sources."""
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from tqdm import tqdm

from src.utils.config import (
    DATA_MONTHS_BACK,
    RAW_DATA_DIR,
    load_media_sources,
)


class MediaScraper:
    """Scraper for traditional media websites."""

    def __init__(self):
        """Initialize the media scraper."""
        self.media_sources = load_media_sources()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def scrape_article(self, url: str) -> Dict:
        """
        Scrape a single article using newspaper3k.

        Args:
            url: Article URL

        Returns:
            Dictionary with article data
        """
        try:
            article = Article(url)
            article.download()
            article.parse()

            return {
                "url": url,
                "title": article.title,
                "text": article.text,
                "publish_date": article.publish_date.isoformat() if article.publish_date else None,
                "authors": article.authors,
                "scraped_at": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None

    def get_rss_articles(self, media_source: Dict) -> List[str]:
        """
        Get article URLs from RSS feed if available.

        Args:
            media_source: Media source configuration

        Returns:
            List of article URLs
        """
        # This is a placeholder - you'll need to implement RSS parsing
        # or sitemap crawling based on each media source's structure
        urls = []

        # Common RSS patterns to try
        rss_patterns = [
            f"{media_source['url']}rss",
            f"{media_source['url']}feed",
            f"{media_source['url']}rss.xml",
            f"{media_source['url']}feed.xml",
        ]

        for rss_url in rss_patterns:
            try:
                response = requests.get(rss_url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "xml")
                    items = soup.find_all("item") or soup.find_all("entry")

                    for item in items:
                        link = item.find("link")
                        if link:
                            url = link.get_text() if link.string else link.get("href")
                            if url:
                                urls.append(url)

                    if urls:
                        print(f"Found {len(urls)} articles from RSS: {rss_url}")
                        break
            except Exception as e:
                continue

        return urls

    def scrape_media_source(self, media_source: Dict, limit: int = 100) -> List[Dict]:
        """
        Scrape articles from a media source.

        Args:
            media_source: Media source configuration
            limit: Maximum number of articles to scrape

        Returns:
            List of article dictionaries
        """
        print(f"Scraping: {media_source['name']}")

        # Try to get articles from RSS
        article_urls = self.get_rss_articles(media_source)

        # If no RSS found, try crawling the homepage
        if not article_urls:
            print(f"No RSS found for {media_source['name']}, skipping...")
            return []

        # Limit the number of articles
        article_urls = article_urls[:limit]

        articles = []
        for url in tqdm(article_urls, desc=f"Scraping {media_source['name']}"):
            article = self.scrape_article(url)
            if article:
                article["source_name"] = media_source["name"]
                article["source_url"] = media_source["url"]
                articles.append(article)

            # Be polite to the server
            time.sleep(1)

        return articles

    def scrape_all_media(self, articles_per_source: int = 100) -> Dict[str, List[Dict]]:
        """
        Scrape all configured media sources.

        Args:
            articles_per_source: Maximum articles per source

        Returns:
            Dictionary mapping media names to their articles
        """
        all_articles = {}

        for media_source in self.media_sources:
            articles = self.scrape_media_source(media_source, limit=articles_per_source)
            all_articles[media_source["name"]] = articles

            # Save individual media data
            safe_name = media_source["name"].replace(" ", "_").replace('"', "").replace("/", "_")
            output_file = RAW_DATA_DIR / f"media_{safe_name}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)

        return all_articles

    def save_all_articles(self, all_articles: Dict[str, List[Dict]]):
        """Save all articles to a single file."""
        output_file = RAW_DATA_DIR / "media_all_articles.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)
        print(f"Saved all articles to {output_file}")


def main():
    """Main function to run the scraper."""
    scraper = MediaScraper()
    all_articles = scraper.scrape_all_media()
    scraper.save_all_articles(all_articles)


if __name__ == "__main__":
    main()
