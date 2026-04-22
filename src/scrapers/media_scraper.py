"""Web scraper for traditional media sources."""
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from tqdm import tqdm

from src.utils.config import (
    RAW_DATA_DIR,
    load_media_sources,
    get_start_date,
)


class MediaScraper:
    """Scraper for traditional media websites."""

    def __init__(self, force_rescrape: bool = False, skip_existing: bool = True):
        """
        Initialize the media scraper.

        Args:
            force_rescrape: If True, rescrape all sources even if data exists
            skip_existing: If True, skip sources that already have data files
        """
        self.media_sources = load_media_sources()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.force_rescrape = force_rescrape
        self.skip_existing = skip_existing
        self.start_date = get_start_date()

    def scrape_article(self, url: str) -> Dict:
        """
        Scrape a single article using newspaper3k.

        Args:
            url: Article URL

        Returns:
            Dictionary with article data, or None if article is too old or error occurs
        """
        try:
            article = Article(url)
            article.download()
            article.parse()

            # Filter by date if publish_date is available
            if article.publish_date:
                # Make publish_date timezone-aware if it isn't
                pub_date = article.publish_date
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)

                # Skip articles older than start_date
                if pub_date < self.start_date:
                    return None

            return {
                "url": url,
                "title": article.title,
                "text": article.text,
                "publish_date": article.publish_date.isoformat() if article.publish_date else None,
                "authors": article.authors,
                "scraped_at": datetime.now().isoformat(),
            }
        except Exception as e:
            # Silently skip failed articles to avoid cluttering output
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
        # Check if data already exists
        safe_name = media_source["name"].replace(" ", "_").replace('"', "").replace("/", "_")
        output_file = RAW_DATA_DIR / f"media_{safe_name}.json"

        if output_file.exists() and self.skip_existing and not self.force_rescrape:
            print(f"⏭️  Skipping {media_source['name']} - data already exists at {output_file}")
            print(f"   Use force_rescrape=True to re-download")
            # Load and return existing data
            with open(output_file, "r", encoding="utf-8") as f:
                existing_articles = json.load(f)
            print(f"   Loaded {len(existing_articles)} existing articles")
            return existing_articles

        print(f"📥 Scraping: {media_source['name']}")
        print(f"   Filtering articles from {self.start_date.date()} onwards")

        # Try to get articles from RSS
        print(f"   🔍 Looking for RSS feed...")
        article_urls = self.get_rss_articles(media_source)

        # If no RSS found, try crawling the homepage
        if not article_urls:
            print(f"   ⚠️  No RSS found for {media_source['name']}, skipping...")
            return []

        print(f"   📄 Found {len(article_urls)} articles in RSS feed")

        # Limit the number of articles
        original_count = len(article_urls)
        article_urls = article_urls[:limit]
        if original_count > limit:
            print(f"   ✂️  Limiting to {limit} most recent articles (from {original_count})")

        articles = []
        skipped_old = 0
        errors = 0

        print(f"   ⬇️  Downloading articles...")
        for idx, url in enumerate(tqdm(article_urls, desc=f"   Articles", unit="art"), 1):
            try:
                article = self.scrape_article(url)
                if article:
                    article["source_name"] = media_source["name"]
                    article["source_url"] = media_source["url"]
                    articles.append(article)
                else:
                    # Article was skipped (too old or error)
                    skipped_old += 1
            except Exception as e:
                errors += 1
                if errors <= 3:  # Only show first 3 errors
                    print(f"      ⚠️  Error on article {idx}: {e}")

            # Be polite to the server
            time.sleep(1)

        print(f"\n   ✅ Collected {len(articles)} articles from {media_source['name']}")
        if skipped_old > 0:
            print(f"   ⏭️  Skipped {skipped_old} articles (too old or failed)")
        if errors > 3:
            print(f"   ⚠️  Total errors: {errors}")

        return articles

    def scrape_all_media(self, articles_per_source: int = 100) -> Dict[str, List[Dict]]:
        """
        Scrape all configured media sources.

        Args:
            articles_per_source: Maximum articles per source

        Returns:
            Dictionary mapping media names to their articles
        """
        print(f"\n📋 Total media sources to process: {len(self.media_sources)}")
        print(f"📅 Start date filter: {self.start_date.date()}")
        print("=" * 60)

        all_articles = {}
        successful = 0
        skipped = 0
        failed = 0

        for idx, media_source in enumerate(self.media_sources, 1):
            print(f"\n[{idx}/{len(self.media_sources)}] Processing: {media_source['name']}")
            print("-" * 60)

            articles = self.scrape_media_source(media_source, limit=articles_per_source)
            all_articles[media_source["name"]] = articles

            # Save individual media data (only if new data was scraped)
            safe_name = media_source["name"].replace(" ", "_").replace('"', "").replace("/", "_")
            output_file = RAW_DATA_DIR / f"media_{safe_name}.json"
            if articles and (not output_file.exists() or self.force_rescrape):
                try:
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(articles, f, ensure_ascii=False, indent=2)
                    file_size = output_file.stat().st_size / 1024  # KB
                    print(f"💾 Saved to {output_file} ({file_size:.2f} KB)")
                    successful += 1
                except Exception as e:
                    print(f"❌ Error saving file: {e}")
                    failed += 1
            elif not articles:
                print(f"⚠️  No articles collected")
                failed += 1
            else:
                skipped += 1

        print("\n" + "=" * 60)
        print("📊 MEDIA SCRAPING SUMMARY")
        print("=" * 60)
        print(f"✅ Successful: {successful}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"❌ Failed/Empty: {failed}")
        print(f"📝 Total: {len(self.media_sources)}")
        print("=" * 60)

        return all_articles

    def save_all_articles(self, all_articles: Dict[str, List[Dict]]):
        """
        Save all articles to a single file.
        Merges with existing data if present to avoid data loss.
        """
        output_file = RAW_DATA_DIR / "media_all_articles.json"

        # Load existing data if present
        existing_data = {}
        if output_file.exists():
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                print(f"📂 Found existing data file with {len(existing_data)} media sources")
            except Exception as e:
                print(f"⚠️  Could not load existing data: {e}")

        # Merge new data with existing (new data takes precedence)
        merged_data = {**existing_data, **all_articles}

        # Create backup before overwriting
        if output_file.exists():
            backup_file = RAW_DATA_DIR / f"media_all_articles_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import shutil
            shutil.copy2(output_file, backup_file)
            print(f"🔄 Created backup at {backup_file}")

        # Save merged data
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)

        total_articles = sum(len(arts) for arts in merged_data.values())
        print(f"💾 Saved all articles to {output_file}")
        print(f"   Total: {len(merged_data)} media sources, {total_articles} articles")


def main():
    """Main function to run the scraper."""
    scraper = MediaScraper()
    all_articles = scraper.scrape_all_media()
    scraper.save_all_articles(all_articles)


if __name__ == "__main__":
    main()
