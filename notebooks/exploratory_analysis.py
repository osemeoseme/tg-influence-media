"""
Exploratory Analysis Script

This script provides examples of how to load and explore the analysis results.
You can run this in a Jupyter notebook or as a standalone script.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set up plotting style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "results"


def load_results():
    """Load analysis results."""
    results_file = RESULTS_DIR / "analysis_all_channels.json"
    with open(results_file, "r", encoding="utf-8") as f:
        return json.load(f)


def create_summary_dataframe(results):
    """Create a summary DataFrame from results."""
    data = []
    for channel_name, result in results.items():
        stats = result["statistics"]
        data.append({
            "Channel": channel_name,
            "Total Messages": stats["total_messages"],
            "Influenced": stats["influenced_by_media"],
            "Percentage": stats["percentage_influenced"],
            "Link Only": stats["detection_breakdown"]["link_only"],
            "Mention Only": stats["detection_breakdown"]["mention_only"],
            "Similarity Only": stats["detection_breakdown"]["similarity_only"],
            "Multiple Methods": stats["detection_breakdown"]["multiple_methods"],
        })
    return pd.DataFrame(data)


def analyze_by_detection_method(results):
    """Analyze which detection methods are most effective."""
    total_links = 0
    total_mentions = 0
    total_similarity = 0

    for result in results.values():
        stats = result["statistics"]
        breakdown = stats["detection_breakdown"]

        total_links += breakdown["link_only"] + breakdown["multiple_methods"]
        total_mentions += breakdown["mention_only"] + breakdown["multiple_methods"]
        total_similarity += breakdown["similarity_only"] + breakdown["multiple_methods"]

    return {
        "Links": total_links,
        "Mentions": total_mentions,
        "Similarity": total_similarity,
    }


def find_top_media_sources(results):
    """Find which media sources are most referenced."""
    media_counts = {}

    for result in results.values():
        for msg in result["messages"]:
            # Count mentioned media
            mentioned = msg.get("mention_detection", {}).get("mentioned_media", [])
            for media in mentioned:
                media_counts[media] = media_counts.get(media, 0) + 1

            # Count similar articles
            similar = msg.get("similarity_detection", {}).get("similar_articles", [])
            for article in similar:
                source = article["article"].get("source_name")
                if source:
                    media_counts[source] = media_counts.get(source, 0) + 1

    return dict(sorted(media_counts.items(), key=lambda x: x[1], reverse=True))


def analyze_temporal_patterns(results):
    """Analyze temporal patterns in media influence."""
    # This requires parsing dates and grouping by time periods
    pass


def main():
    """Run exploratory analysis."""
    print("Loading results...")
    results = load_results()

    # Create summary DataFrame
    df = create_summary_dataframe(results)
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print(df.to_string(index=False))

    # Overall statistics
    total_messages = df["Total Messages"].sum()
    total_influenced = df["Influenced"].sum()
    overall_percentage = (total_influenced / total_messages * 100) if total_messages > 0 else 0

    print(f"\nOverall: {total_influenced:,} / {total_messages:,} messages influenced ({overall_percentage:.2f}%)")

    # Detection method effectiveness
    print("\n" + "="*80)
    print("DETECTION METHOD EFFECTIVENESS")
    print("="*80)
    method_stats = analyze_by_detection_method(results)
    for method, count in method_stats.items():
        print(f"{method}: {count:,} messages")

    # Top media sources
    print("\n" + "="*80)
    print("TOP REFERENCED MEDIA SOURCES")
    print("="*80)
    media_sources = find_top_media_sources(results)
    for i, (source, count) in enumerate(media_sources.items(), 1):
        if i <= 10:  # Top 10
            print(f"{i:2d}. {source}: {count:,} references")

    # Create visualizations
    print("\n" + "="*80)
    print("CREATING VISUALIZATIONS")
    print("="*80)

    # Plot 1: Media influence by channel
    plt.figure(figsize=(12, 6))
    df_sorted = df.sort_values("Percentage", ascending=True)
    plt.barh(df_sorted["Channel"], df_sorted["Percentage"])
    plt.xlabel("Percentage of Messages Influenced (%)")
    plt.title("Media Influence by Telegram Channel")
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "influence_by_channel.png", dpi=300, bbox_inches="tight")
    print("Saved: influence_by_channel.png")

    # Plot 2: Detection method distribution
    plt.figure(figsize=(10, 6))
    methods = list(method_stats.keys())
    counts = list(method_stats.values())
    plt.bar(methods, counts)
    plt.ylabel("Number of Messages")
    plt.title("Messages Detected by Each Method")
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "detection_methods.png", dpi=300, bbox_inches="tight")
    print("Saved: detection_methods.png")

    # Plot 3: Top media sources
    plt.figure(figsize=(12, 8))
    top_sources = dict(list(media_sources.items())[:15])
    plt.barh(list(top_sources.keys()), list(top_sources.values()))
    plt.xlabel("Number of References")
    plt.title("Top 15 Referenced Media Sources")
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "top_media_sources.png", dpi=300, bbox_inches="tight")
    print("Saved: top_media_sources.png")

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
