"""Generate reports and visualizations from analysis results."""
import json
from pathlib import Path
from typing import Dict, List
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.utils.config import RESULTS_DIR


class ReportGenerator:
    """Generate reports and visualizations."""

    def __init__(self):
        """Initialize the report generator."""
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)

    def generate_summary_report(self, all_results: Dict[str, Dict]) -> str:
        """
        Generate a text summary report.

        Args:
            all_results: Dictionary mapping channel names to their results

        Returns:
            Summary report as string
        """
        report = []
        report.append("=" * 80)
        report.append("MEDIA INFLUENCE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")

        # Overall statistics
        total_messages = sum(
            r["statistics"]["total_messages"] for r in all_results.values()
        )
        total_influenced = sum(
            r["statistics"]["influenced_by_media"] for r in all_results.values()
        )
        overall_percentage = (total_influenced / total_messages * 100) if total_messages > 0 else 0

        report.append("OVERALL STATISTICS")
        report.append("-" * 80)
        report.append(f"Total messages analyzed: {total_messages:,}")
        report.append(f"Messages influenced by media: {total_influenced:,}")
        report.append(f"Percentage influenced: {overall_percentage:.2f}%")
        report.append("")

        # Per-channel statistics
        report.append("PER-CHANNEL STATISTICS")
        report.append("-" * 80)

        for channel_name, results in all_results.items():
            stats = results["statistics"]
            report.append(f"\n{channel_name}")
            report.append(f"  Total messages: {stats['total_messages']:,}")
            report.append(f"  Influenced by media: {stats['influenced_by_media']:,} "
                         f"({stats['percentage_influenced']:.2f}%)")

            # Detection method breakdown
            breakdown = stats["detection_breakdown"]
            report.append(f"  Detection breakdown:")
            report.append(f"    - Link only: {breakdown['link_only']}")
            report.append(f"    - Mention only: {breakdown['mention_only']}")
            report.append(f"    - Similarity only: {breakdown['similarity_only']}")
            report.append(f"    - Multiple methods: {breakdown['multiple_methods']}")

            # Content type distribution (if available)
            if 'content_types' in stats:
                content_types = stats['content_types']
                report.append(f"  Content type distribution:")
                for ct, pct in content_types.get('content_type_percentages', {}).items():
                    count = content_types['content_type_counts'].get(ct, 0)
                    if pct > 0:
                        report.append(f"    - {ct}: {count} ({pct:.1f}%)")

            # Non-media references (if available)
            if 'references' in stats:
                ref_stats = stats['references']
                report.append(f"  Non-media references:")
                report.append(f"    - Messages with non-media refs: {ref_stats.get('messages_with_non_media_references', 0)}")
                report.append(f"    - Unique Telegram channels mentioned: {ref_stats.get('unique_telegram_channels_mentioned', 0)}")
                if ref_stats.get('reference_category_counts'):
                    report.append(f"    - Reference categories:")
                    for category, count in ref_stats['reference_category_counts'].items():
                        report.append(f"      • {category}: {count}")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def create_visualizations(self, all_results: Dict[str, Dict]):
        """
        Create visualizations from analysis results.

        Args:
            all_results: Dictionary mapping channel names to their results
        """
        # Prepare data for visualization
        data = []
        for channel_name, results in all_results.items():
            stats = results["statistics"]
            data.append({
                "Channel": channel_name[:30],  # Truncate long names
                "Total": stats["total_messages"],
                "Influenced": stats["influenced_by_media"],
                "Percentage": stats["percentage_influenced"],
            })

        df = pd.DataFrame(data)

        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle("Media Influence Analysis", fontsize=16, fontweight='bold')

        # 1. Bar chart: Percentage influenced by channel
        ax1 = axes[0, 0]
        df_sorted = df.sort_values("Percentage", ascending=True)
        ax1.barh(df_sorted["Channel"], df_sorted["Percentage"], color='steelblue', alpha=0.8)
        ax1.set_xlabel("Percentage (%)", fontsize=11, fontweight='bold')
        ax1.set_title("Media Influence by Channel", fontsize=13, fontweight='bold', pad=10)
        ax1.grid(axis='x', alpha=0.3)
        ax1.set_xlim(0, max(100, df_sorted["Percentage"].max() * 1.1))

        # 2. Stacked bar chart: Total vs Influenced
        ax2 = axes[0, 1]
        df_sorted = df.sort_values("Influenced", ascending=True)
        x_pos = range(len(df_sorted))
        ax2.barh(x_pos, df_sorted["Total"],
                label='Total Messages', color='lightgray', alpha=0.6)
        ax2.barh(x_pos, df_sorted["Influenced"],
                label='Influenced by Media', color='steelblue', alpha=0.8)
        ax2.set_yticks(x_pos)
        ax2.set_yticklabels(df_sorted["Channel"], fontsize=9)
        ax2.set_xlabel("Number of Messages", fontsize=11, fontweight='bold')
        ax2.set_title("Messages: Total vs Influenced", fontsize=13, fontweight='bold', pad=10)
        ax2.legend(fontsize=9)
        ax2.grid(axis='x', alpha=0.3)

        # 3. Detection method breakdown
        ax3 = axes[1, 0]
        breakdown_data = []
        for channel_name, results in all_results.items():
            breakdown = results["statistics"]["detection_breakdown"]
            breakdown_data.append({
                "Channel": channel_name[:30],
                "Links": breakdown["link_only"],
                "Mentions": breakdown["mention_only"],
                "Similarity": breakdown["similarity_only"],
                "Multiple": breakdown["multiple_methods"],
            })

        df_breakdown = pd.DataFrame(breakdown_data)
        df_breakdown = df_breakdown.sort_values(by=['Links', 'Mentions', 'Similarity', 'Multiple'], ascending=True)
        df_breakdown.set_index("Channel").plot(kind='barh', stacked=True, ax=ax3,
                                               color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'],
                                               alpha=0.8)
        ax3.set_title("Detection Method Breakdown by Channel", fontsize=13, fontweight='bold', pad=10)
        ax3.set_xlabel("Number of Messages", fontsize=11, fontweight='bold')
        ax3.legend(title="Detection Method", fontsize=9, title_fontsize=9)
        ax3.grid(axis='x', alpha=0.3)

        # 4. Overall pie chart
        ax4 = axes[1, 1]
        total_messages = df["Total"].sum()
        total_influenced = df["Influenced"].sum()
        total_not_influenced = total_messages - total_influenced

        wedges, texts, autotexts = ax4.pie([total_influenced, total_not_influenced],
               labels=[f'Influenced by Media\n({total_influenced:,})',
                      f'Not Influenced\n({total_not_influenced:,})'],
               autopct='%1.1f%%', startangle=90,
               colors=['steelblue', 'lightgray'],
               explode=(0.05, 0))

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(11)

        ax4.set_title("Overall Media Influence Distribution", fontsize=13, fontweight='bold', pad=10)

        plt.tight_layout()

        # Save figure
        output_file = RESULTS_DIR / "analysis_visualizations.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Visualizations saved to: {output_file}")

        plt.close()

    def export_to_csv(self, all_results: Dict[str, Dict]):
        """
        Export results to CSV files.

        Args:
            all_results: Dictionary mapping channel names to their results
        """
        # Summary CSV
        summary_data = []
        for channel_name, results in all_results.items():
            stats = results["statistics"]
            breakdown = stats["detection_breakdown"]

            summary_data.append({
                "Channel": channel_name,
                "Total Messages": stats["total_messages"],
                "Influenced by Media": stats["influenced_by_media"],
                "Percentage Influenced": stats["percentage_influenced"],
                "Link Only": breakdown["link_only"],
                "Mention Only": breakdown["mention_only"],
                "Similarity Only": breakdown["similarity_only"],
                "Multiple Methods": breakdown["multiple_methods"],
            })

        df_summary = pd.DataFrame(summary_data)
        summary_file = RESULTS_DIR / "summary.csv"
        df_summary.to_csv(summary_file, index=False, encoding="utf-8")
        print(f"Summary CSV saved to: {summary_file}")

        # Detailed CSV with all messages
        detailed_data = []
        for channel_name, results in all_results.items():
            for msg in results["messages"]:
                detailed_data.append({
                    "Channel": channel_name,
                    "Message ID": msg["id"],
                    "Date": msg["date"],
                    "Text": msg.get("text", "")[:200],  # Truncate text
                    "Has Link": msg.get("link_detection", {}).get("has_media_link", False),
                    "Has Mention": msg.get("mention_detection", {}).get("has_media_mention", False),
                    "Has Similarity": msg.get("similarity_detection", {}).get("has_similar_content", False),
                    "Media URLs": ", ".join(msg.get("link_detection", {}).get("media_urls", [])),
                    "Mentioned Media": ", ".join(msg.get("mention_detection", {}).get("mentioned_media", [])),
                })

        df_detailed = pd.DataFrame(detailed_data)
        detailed_file = RESULTS_DIR / "detailed_messages.csv"
        df_detailed.to_csv(detailed_file, index=False, encoding="utf-8")
        print(f"Detailed CSV saved to: {detailed_file}")

    def generate_full_report(self, all_results: Dict[str, Dict]):
        """
        Generate full report with summary, visualizations, and exports.

        Args:
            all_results: Dictionary mapping channel names to their results
        """
        print("\n" + "=" * 80)
        print("GENERATING REPORTS")
        print("=" * 80)

        # Generate text summary
        summary = self.generate_summary_report(all_results)
        print(summary)

        # Save summary to file
        summary_file = RESULTS_DIR / "report.txt"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"\nText report saved to: {summary_file}")

        # Create visualizations
        self.create_visualizations(all_results)

        # Export to CSV
        self.export_to_csv(all_results)

        print("\n" + "=" * 80)
        print("REPORT GENERATION COMPLETE")
        print("=" * 80)
