"""
Custom Analysis Examples

This script demonstrates how to use the project modules for custom analysis tasks.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzers.link_detector import LinkDetector
from src.analyzers.mention_detector import MentionDetector
from src.analyzers.similarity_detector import SimilarityDetector
from src.utils.config import RAW_DATA_DIR


def example_1_analyze_single_message():
    """Example: Analyze a single Telegram message."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Analyze a Single Message")
    print("="*80)

    # Sample message
    message = {
        "id": 12345,
        "date": "2026-04-01T10:30:00",
        "text": "За даними Української правди, сьогодні відбулася важлива подія. Детальніше: https://pravda.com.ua/news/2026/04/1/article/",
        "urls": ["https://pravda.com.ua/news/2026/04/1/article/"],
    }

    # Link detection
    link_detector = LinkDetector()
    link_result = link_detector.detect_media_links(message)
    print(f"\nLink Detection:")
    print(f"  Has media link: {link_result['has_media_link']}")
    print(f"  Media URLs: {link_result['media_urls']}")

    # Mention detection
    mention_detector = MentionDetector()
    mention_result = mention_detector.detect_mentions(message)
    print(f"\nMention Detection:")
    print(f"  Has media mention: {mention_result['has_media_mention']}")
    print(f"  Mentioned media: {mention_result['mentioned_media']}")


def example_2_analyze_channel_subset():
    """Example: Analyze a subset of messages from a channel."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Analyze Channel Subset")
    print("="*80)

    # Load data
    telegram_file = RAW_DATA_DIR / "telegram_truexanewsua.json"
    if not telegram_file.exists():
        print("Data file not found. Run 'python main.py scrape' first.")
        return

    with open(telegram_file, "r", encoding="utf-8") as f:
        messages = json.load(f)

    # Analyze first 100 messages
    messages_subset = messages[:100]
    print(f"\nAnalyzing {len(messages_subset)} messages...")

    # Link detection
    link_detector = LinkDetector()
    analyzed = link_detector.analyze_messages(messages_subset)
    stats = link_detector.get_statistics(analyzed)

    print(f"\nResults:")
    print(f"  Total: {stats['total_messages']}")
    print(f"  With media links: {stats['messages_with_media_links']} "
          f"({stats['percentage_with_media_links']:.2f}%)")


def example_3_find_similar_content():
    """Example: Find similar content between a message and articles."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Find Similar Content")
    print("="*80)

    # Sample message
    message = {
        "id": 12345,
        "date": "2026-04-01T12:00:00",
        "text": "Сьогодні в Києві відбулася важлива зустріч представників влади та бізнесу. "
                "Обговорювалися питання економічного розвитку та інвестицій. "
                "Учасники досягли домовленостей щодо створення нових робочих місць.",
    }

    # Sample articles
    articles = [
        {
            "title": "Зустріч влади та бізнесу в Києві",
            "text": "У столиці пройшла зустріч, на якій обговорювалися питання економіки. "
                    "Представники бізнесу та уряду домовилися про створення робочих місць.",
            "publish_date": "2026-04-01T10:00:00",
            "source_name": "Українська правда",
        },
        {
            "title": "Погода в Києві",
            "text": "Сьогодні в Києві очікується хмарна погода з невеликими опадами.",
            "publish_date": "2026-04-01T08:00:00",
            "source_name": "Суспільне",
        },
    ]

    # Find similar articles
    print("\nLoading similarity model (this may take a moment)...")
    similarity_detector = SimilarityDetector()

    print("Computing similarities...")
    media_texts = [f"{a['title']} {a['text']}" for a in articles]
    media_embeddings = similarity_detector.encode_texts(media_texts)

    similar = similarity_detector.find_similar_articles(
        message, articles, media_embeddings
    )

    print(f"\nFound {len(similar)} similar articles:")
    for i, item in enumerate(similar, 1):
        print(f"\n{i}. {item['article']['source_name']}")
        print(f"   Similarity: {item['similarity_score']:.3f}")
        print(f"   Title: {item['article']['title']}")


def example_4_compare_channels():
    """Example: Compare media influence across channels."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Compare Channels")
    print("="*80)

    # Load results
    results_file = Path(__file__).parent.parent / "data" / "results" / "analysis_all_channels.json"
    if not results_file.exists():
        print("Results file not found. Run 'python main.py analyze' first.")
        return

    with open(results_file, "r", encoding="utf-8") as f:
        all_results = json.load(f)

    # Compare channels
    print("\nMedia Influence Comparison:")
    print(f"{'Channel':<40} {'Total':<10} {'Influenced':<12} {'Percentage':<12}")
    print("-" * 80)

    for channel_name, results in all_results.items():
        stats = results["statistics"]
        print(f"{channel_name[:39]:<40} "
              f"{stats['total_messages']:<10} "
              f"{stats['influenced_by_media']:<12} "
              f"{stats['percentage_influenced']:>10.2f}%")


def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("CUSTOM ANALYSIS EXAMPLES")
    print("="*80)

    # Run examples
    example_1_analyze_single_message()

    # Uncomment to run other examples (require data to be scraped first)
    # example_2_analyze_channel_subset()
    # example_3_find_similar_content()
    # example_4_compare_channels()

    print("\n" + "="*80)
    print("EXAMPLES COMPLETE")
    print("="*80)
    print("\nTo run other examples, make sure to:")
    print("1. Scrape data: python main.py scrape")
    print("2. Analyze data: python main.py analyze")
    print("3. Uncomment example functions in this script")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
