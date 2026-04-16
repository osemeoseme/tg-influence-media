"""Main script to run the media influence analysis."""
import argparse
import asyncio
import json
import sys
from pathlib import Path

from src.scrapers.telegram_scraper import TelegramScraper
from src.scrapers.media_scraper import MediaScraper
from src.analyzers.combined_analyzer import CombinedAnalyzer
from src.processors.report_generator import ReportGenerator
from src.utils.config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    RESULTS_DIR,
    load_telegram_channels,
)


def scrape_data():
    """Scrape data from Telegram and media sources."""
    print("\n" + "=" * 80)
    print("DATA COLLECTION PHASE")
    print("=" * 80)

    # Scrape Telegram channels
    print("\n[1/2] Scraping Telegram channels...")
    telegram_scraper = TelegramScraper()
    asyncio.run(telegram_scraper.scrape_all_channels())

    # Scrape media sources
    print("\n[2/2] Scraping media sources...")
    media_scraper = MediaScraper()
    media_scraper.scrape_all_media(articles_per_source=100)

    print("\n" + "=" * 80)
    print("DATA COLLECTION COMPLETE")
    print("=" * 80)


def load_scraped_data():
    """Load scraped data from files."""
    # Load Telegram data
    telegram_file = RAW_DATA_DIR / "telegram_all_messages.json"
    if not telegram_file.exists():
        print(f"Error: {telegram_file} not found. Run 'python main.py scrape' first.")
        sys.exit(1)

    with open(telegram_file, "r", encoding="utf-8") as f:
        telegram_data = json.load(f)

    # Load media data
    media_file = RAW_DATA_DIR / "media_all_articles.json"
    if not media_file.exists():
        print(f"Error: {media_file} not found. Run 'python main.py scrape' first.")
        sys.exit(1)

    with open(media_file, "r", encoding="utf-8") as f:
        media_data = json.load(f)

    # Flatten media data
    all_articles = []
    for source_articles in media_data.values():
        all_articles.extend(source_articles)

    return telegram_data, all_articles


def analyze_data():
    """Analyze the scraped data."""
    print("\n" + "=" * 80)
    print("ANALYSIS PHASE")
    print("=" * 80)

    # Load data
    print("\nLoading scraped data...")
    telegram_data, media_articles = load_scraped_data()

    print(f"Loaded {len(telegram_data)} Telegram channels")
    print(f"Loaded {len(media_articles)} media articles")

    # Analyze each channel
    analyzer = CombinedAnalyzer()
    all_results = {}

    channels = load_telegram_channels()

    for channel in channels:
        username = channel["username"]
        name = channel["name"]

        if username not in telegram_data:
            print(f"\nSkipping {name} - no data found")
            continue

        messages = telegram_data[username]
        if not messages:
            print(f"\nSkipping {name} - no messages")
            continue

        # Analyze channel
        results = analyzer.analyze_channel(messages, media_articles, name)
        all_results[name] = results

        # Save individual channel results
        safe_name = name.replace(" ", "_").replace('"', "").replace("/", "_")
        output_file = RESULTS_DIR / f"analysis_{safe_name}.json"
        analyzer.save_results(results, output_file)

    # Save combined results
    combined_file = RESULTS_DIR / "analysis_all_channels.json"
    with open(combined_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\nCombined results saved to: {combined_file}")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

    return all_results


def generate_report():
    """Generate reports from analysis results."""
    print("\n" + "=" * 80)
    print("REPORT GENERATION PHASE")
    print("=" * 80)

    # Load analysis results
    results_file = RESULTS_DIR / "analysis_all_channels.json"
    if not results_file.exists():
        print(f"Error: {results_file} not found. Run 'python main.py analyze' first.")
        sys.exit(1)

    with open(results_file, "r", encoding="utf-8") as f:
        all_results = json.load(f)

    # Generate report
    report_gen = ReportGenerator()
    report_gen.generate_full_report(all_results)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze the influence of traditional media on Telegram channels"
    )
    parser.add_argument(
        "command",
        choices=["scrape", "analyze", "report", "all"],
        help="Command to execute",
    )

    args = parser.parse_args()

    if args.command == "scrape":
        scrape_data()
    elif args.command == "analyze":
        analyze_data()
    elif args.command == "report":
        generate_report()
    elif args.command == "all":
        scrape_data()
        analyze_data()
        generate_report()


if __name__ == "__main__":
    main()
