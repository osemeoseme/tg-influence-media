"""Main script to run the media influence analysis."""
import argparse
import asyncio
import json
import sys
from pathlib import Path

from src.scrapers.telegram_scraper import TelegramScraper
from src.scrapers.media_scraper import MediaScraper
from src.analyzers.combined_analyzer import CombinedAnalyzer
from src.analyzers.bidirectional_influence import BidirectionalInfluenceAnalyzer
from src.processors.report_generator import ReportGenerator
from src.processors.interactive_visualizations import InteractiveVisualizer
from src.utils.config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    RESULTS_DIR,
    load_telegram_channels,
)


def scrape_data(force_rescrape=False):
    """
    Scrape data from Telegram and media sources.

    Args:
        force_rescrape: If True, re-download all data even if it exists
    """
    from datetime import datetime
    start_time = datetime.now()

    print("\n" + "=" * 80)
    print("🚀 DATA COLLECTION PHASE")
    print("=" * 80)
    print(f"⏰ Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    if force_rescrape:
        print("\n⚠️  FORCE RESCRAPE MODE: Will re-download all data")
        print("   ⚡ This will take longer but ensures fresh data")
        print("   💾 Backups will be created before overwriting")
    else:
        print("\n📁 SMART MODE: Will skip channels/sources with existing data")
        print("   ⚡ This is fast if data already exists")
        print("   💡 Use --force to re-download everything")

    # Scrape Telegram channels
    print("\n" + "=" * 80)
    print("📱 [1/2] TELEGRAM CHANNELS")
    print("=" * 80)
    tg_start = datetime.now()

    telegram_scraper = TelegramScraper(
        force_rescrape=force_rescrape,
        skip_existing=not force_rescrape
    )
    all_tg_messages = asyncio.run(telegram_scraper.scrape_all_channels())
    telegram_scraper.save_all_messages(all_tg_messages)

    tg_duration = (datetime.now() - tg_start).total_seconds()
    print(f"\n⏱️  Telegram scraping took: {tg_duration:.1f} seconds ({tg_duration/60:.1f} minutes)")

    # Scrape media sources
    print("\n" + "=" * 80)
    print("📰 [2/2] MEDIA SOURCES")
    print("=" * 80)
    media_start = datetime.now()

    media_scraper = MediaScraper(
        force_rescrape=force_rescrape,
        skip_existing=not force_rescrape
    )
    all_articles = media_scraper.scrape_all_media(articles_per_source=100)
    media_scraper.save_all_articles(all_articles)

    media_duration = (datetime.now() - media_start).total_seconds()
    print(f"\n⏱️  Media scraping took: {media_duration:.1f} seconds ({media_duration/60:.1f} minutes)")

    # Final summary
    total_duration = (datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 80)
    print("✅ DATA COLLECTION COMPLETE")
    print("=" * 80)
    print(f"⏰ Total time: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
    print(f"📊 Telegram channels: {len(all_tg_messages)}")
    total_tg_msgs = sum(len(msgs) for msgs in all_tg_messages.values())
    print(f"📨 Total Telegram messages: {total_tg_msgs:,}")
    print(f"📰 Media sources: {len(all_articles)}")
    total_articles = sum(len(arts) for arts in all_articles.values())
    print(f"📄 Total articles: {total_articles:,}")
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

        # Add channel name to each message for later analysis
        for msg in messages:
            msg['channel_name'] = name

        # Analyze channel
        results = analyzer.analyze_channel(messages, media_articles, name)
        all_results[name] = results

        # Save individual channel results
        safe_name = name.replace(" ", "_").replace('"', "").replace("/", "_")
        output_file = RESULTS_DIR / f"analysis_{safe_name}.json"
        analyzer.save_results(results, output_file)

    # Perform bidirectional influence analysis
    print("\n" + "=" * 80)
    print("BIDIRECTIONAL INFLUENCE ANALYSIS")
    print("=" * 80)

    # Collect all analyzed messages
    all_analyzed_messages = []
    for results in all_results.values():
        all_analyzed_messages.extend(results['messages'])

    bidirectional_analyzer = BidirectionalInfluenceAnalyzer()
    bidirectional_results = bidirectional_analyzer.generate_full_analysis(
        all_analyzed_messages, media_articles
    )

    # Save bidirectional analysis results
    bidirectional_file = RESULTS_DIR / "bidirectional_influence.json"
    with open(bidirectional_file, "w", encoding="utf-8") as f:
        json.dump(bidirectional_results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nBidirectional analysis saved to: {bidirectional_file}")

    # Save combined results with bidirectional data
    combined_data = {
        "channel_results": all_results,
        "bidirectional_influence": bidirectional_results
    }
    combined_file = RESULTS_DIR / "analysis_all_channels.json"
    with open(combined_file, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nCombined results saved to: {combined_file}")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

    return all_results, bidirectional_results


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
        combined_data = json.load(f)

    # Handle both old and new format
    if "channel_results" in combined_data:
        all_results = combined_data["channel_results"]
        bidirectional_results = combined_data.get("bidirectional_influence")
    else:
        all_results = combined_data
        bidirectional_results = None

    # Generate report
    report_gen = ReportGenerator()
    report_gen.generate_full_report(all_results)

    # Generate interactive visualizations
    print("\n" + "=" * 80)
    print("INTERACTIVE VISUALIZATIONS")
    print("=" * 80)

    visualizer = InteractiveVisualizer()
    visualizer.save_all_visualizations(all_results, bidirectional_results)


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
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-scrape all data even if it already exists (default: skip existing)",
    )

    args = parser.parse_args()

    if args.command == "scrape":
        scrape_data(force_rescrape=args.force)
    elif args.command == "analyze":
        all_results, bidirectional_results = analyze_data()
    elif args.command == "report":
        generate_report()
    elif args.command == "all":
        scrape_data(force_rescrape=args.force)
        all_results, bidirectional_results = analyze_data()
        generate_report()


if __name__ == "__main__":
    main()
