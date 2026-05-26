"""Extended static visualizations for deeper insights.

Creates additional PNG visualizations highlighting key findings:
- Content type distribution across channels
- Top referenced Telegram channels
- Non-media reference breakdown
- Bidirectional influence comparison
- Channel ecosystem network
"""
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from collections import Counter
from pathlib import Path
from typing import Dict, List

from src.utils.config import RESULTS_DIR


class ExtendedVisualizer:
    """Create extended static visualizations for key insights."""

    # Channels with insufficient data (redirects to private channels)
    EXCLUDED_CHANNELS = [
        'Україна 24/7 - новини',
        'Інсайдер ЗСУ'
    ]

    def __init__(self):
        """Initialize the extended visualizer."""
        sns.set_style("whitegrid")
        sns.set_palette("husl")
        self.output_dir = RESULTS_DIR

    def _filter_channels(self, all_results: Dict) -> Dict:
        """
        Filter out channels with insufficient data.

        Args:
            all_results: Analysis results for all channels

        Returns:
            Filtered results dictionary
        """
        return {
            channel_name: results
            for channel_name, results in all_results.items()
            if channel_name not in self.EXCLUDED_CHANNELS
        }

    def create_content_type_heatmap(self, all_results: Dict):
        """
        Create heatmap showing content type distribution across channels.

        Args:
            all_results: Analysis results for all channels
        """
        # Filter out excluded channels
        all_results = self._filter_channels(all_results)

        # Prepare data
        channels = []
        content_types = set()

        # First pass - collect all content types
        for channel_name, results in all_results.items():
            stats = results.get('statistics', {})
            ct_stats = stats.get('content_types', {})
            percentages = ct_stats.get('content_type_percentages', {})
            content_types.update(percentages.keys())

        content_types = sorted(list(content_types))

        # Second pass - build matrix
        data = []
        for channel_name, results in all_results.items():
            stats = results.get('statistics', {})
            ct_stats = stats.get('content_types', {})
            percentages = ct_stats.get('content_type_percentages', {})

            row = [percentages.get(ct, 0) for ct in content_types]
            data.append(row)
            channels.append(channel_name[:25])  # Truncate long names

        # Create heatmap
        fig, ax = plt.subplots(figsize=(12, 10))

        df = pd.DataFrame(data, index=channels, columns=content_types)
        sns.heatmap(df, annot=True, fmt='.1f', cmap='YlOrRd',
                    cbar_kws={'label': 'Percentage (%)'}, ax=ax)

        ax.set_title('Content Type Distribution Across Channels',
                     fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Content Type', fontsize=12, fontweight='bold')
        ax.set_ylabel('Channel', fontsize=12, fontweight='bold')

        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()

        output_file = self.output_dir / "content_type_heatmap.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()

    def create_top_telegram_channels_chart(self, all_results: Dict):
        """
        Create bar chart of most referenced Telegram channels.

        Args:
            all_results: Analysis results for all channels
        """
        # Filter out excluded channels
        all_results = self._filter_channels(all_results)

        # Aggregate all mentioned channels
        channel_counts = Counter()

        for channel_name, results in all_results.items():
            for msg in results.get('messages', []):
                ref_detection = msg.get('reference_detection', {})
                for ch in ref_detection.get('telegram_channels', []):
                    channel_counts[ch] += 1

        # Get top 30
        top_channels = channel_counts.most_common(30)

        if not top_channels:
            print("⚠️  No Telegram channel references found")
            return

        # Self-reference and bot patterns to filter out
        EXCLUDED_PATTERNS = [
            'joinchat', 'PromotionMonako', 'nikitos077',
            'addstickers', 'share', 'proxy', 'socks',
            'setlanguage', 'bot', '_bot', 'Bot'
        ]

        # Filter out self-references, promotion bots, and short names
        filtered = []
        for ch, cnt in top_channels:
            # Skip if too short
            if len(ch) <= 2:
                continue
            # Skip if matches excluded patterns
            if any(pattern.lower() in ch.lower() for pattern in EXCLUDED_PATTERNS):
                continue
            filtered.append((ch, cnt))
            if len(filtered) >= 20:
                break

        channels, counts = zip(*filtered)

        # Create horizontal bar chart
        fig, ax = plt.subplots(figsize=(12, 10))

        y_pos = np.arange(len(channels))
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(channels)))

        bars = ax.barh(y_pos, counts, color=colors)

        # Add value labels
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(count + max(counts)*0.01, i, f'{count:,}',
                   va='center', fontsize=9)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(channels, fontsize=10)
        ax.set_xlabel('Number of Mentions', fontsize=12, fontweight='bold')
        ax.set_title('Top 20 Most Referenced Telegram Channels',
                     fontsize=16, fontweight='bold', pad=20)
        ax.invert_yaxis()
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()

        output_file = self.output_dir / "top_telegram_channels.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()

    def create_reference_category_breakdown(self, all_results: Dict):
        """
        Create pie charts showing reference category breakdown including traditional media.

        Args:
            all_results: Analysis results for all channels
        """
        # Filter out excluded channels
        all_results = self._filter_channels(all_results)

        # Aggregate reference categories (non-media)
        category_counts = Counter()

        for channel_name, results in all_results.items():
            stats = results.get('statistics', {})
            ref_stats = stats.get('references', {})
            ref_cats = ref_stats.get('reference_category_counts', {})

            for category, count in ref_cats.items():
                category_counts[category] += count

        # Add traditional media references count (IMPORTANT: this shows media contribution)
        traditional_media_count = 0
        for channel_name, results in all_results.items():
            stats = results.get('statistics', {})
            # Count messages influenced by media
            influenced = stats.get('influenced_by_media', 0)
            traditional_media_count += influenced

        # Always add Traditional Media to show complete picture
        category_counts['Traditional Media'] = traditional_media_count

        if not category_counts:
            print("⚠️  No reference categories found")
            return

        # Filter out "Other" categories and group them
        main_categories = {}
        other_count = 0

        for cat, count in category_counts.items():
            if cat.startswith('Other'):
                other_count += count
            else:
                main_categories[cat] = count

        if other_count > 0:
            main_categories['Other domains'] = other_count

        # Create pie chart
        fig, ax = plt.subplots(figsize=(12, 8))

        labels = list(main_categories.keys())
        sizes = list(main_categories.values())

        # Create custom color scheme with Traditional Media highlighted
        colors_list = []
        for label in labels:
            if label == 'Traditional Media':
                colors_list.append('#3498db')  # Blue for traditional media (stands out)
            elif label == 'Telegram Channels':
                colors_list.append('#2ecc71')  # Green for telegram
            elif label == 'YouTube':
                colors_list.append('#e74c3c')  # Red for youtube
            elif label == 'Facebook':
                colors_list.append('#9b59b6')  # Purple for facebook
            elif label == 'Other domains':
                colors_list.append('#f39c12')  # Orange/yellow for other
            else:
                colors_list.append('#95a5a6')  # Gray for smaller categories

        colors = colors_list

        # Create pie with explode for top categories (including Traditional Media)
        total = sum(sizes)
        explode = []
        for label, size in zip(labels, sizes):
            if label == 'Traditional Media':
                explode.append(0.1)  # Emphasize Traditional Media more
            elif size/total > 0.15:
                explode.append(0.05)
            else:
                explode.append(0)

        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                           colors=colors, explode=explode,
                                           startangle=90, textprops={'fontsize': 10})

        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax.set_title('Complete Reference Distribution\n(All sources cited by channels: Traditional Media + Other References)',
                     fontsize=16, fontweight='bold', pad=20)

        # Add legend with counts
        legend_labels = [f'{label}: {count:,}' for label, count in zip(labels, sizes)]
        ax.legend(legend_labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1),
                 fontsize=10)

        plt.tight_layout()

        output_file = self.output_dir / "reference_categories.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()

    def create_media_vs_nonmedia_comparison(self, all_results: Dict):
        """
        Create comparison chart of media vs non-media influence.

        Args:
            all_results: Analysis results for all channels
        """
        # Filter out excluded channels
        all_results = self._filter_channels(all_results)

        # Prepare data
        data = []

        for channel_name, results in all_results.items():
            stats = results.get('statistics', {})
            total = stats.get('total_messages', 0)
            influenced = stats.get('influenced_by_media', 0)

            ref_stats = stats.get('references', {})
            with_nonmedia = ref_stats.get('messages_with_non_media_references', 0)

            data.append({
                'Channel': channel_name[:25],
                'Media Influenced': influenced,
                'Non-Media References': with_nonmedia,
                'No References': total - influenced - with_nonmedia + \
                                (influenced if influenced > 0 else 0)  # Adjust for overlap
            })

        df = pd.DataFrame(data)

        # Create stacked horizontal bar chart
        fig, ax = plt.subplots(figsize=(14, 10))

        channels = df['Channel']
        media = df['Media Influenced']
        nonmedia = df['Non-Media References']

        y_pos = np.arange(len(channels))

        ax.barh(y_pos, media, label='Media Influenced', color='#3498db', alpha=0.8)
        ax.barh(y_pos, nonmedia, left=media, label='Non-Media References',
               color='#e74c3c', alpha=0.8)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(channels, fontsize=10)
        ax.set_xlabel('Number of Messages', fontsize=12, fontweight='bold')
        ax.set_title('Media vs Non-Media Source References by Channel',
                     fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='lower right', fontsize=11)
        ax.grid(axis='x', alpha=0.3)
        ax.invert_yaxis()

        plt.tight_layout()

        output_file = self.output_dir / "media_vs_nonmedia.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()

    def create_bidirectional_influence_chart(self, bidirectional_results: Dict):
        """
        Create visualization comparing Media→Telegram vs Telegram→Media influence.

        Args:
            bidirectional_results: Bidirectional analysis results
        """
        if not bidirectional_results:
            print("⚠️  No bidirectional analysis results")
            return

        comparison = bidirectional_results.get('comparison', {})

        # Extract data
        media_to_tg = comparison.get('media_to_telegram', {})
        tg_to_media = comparison.get('telegram_to_media', {})

        media_refs = media_to_tg.get('total_references', 0)
        tg_citations = tg_to_media.get('total_citations', 0)

        top_media = media_to_tg.get('top_influencers', [])[:10]
        top_channels = tg_to_media.get('top_influencers', [])[:10]

        # Create figure with subplots
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

        # 1. Overall comparison pie chart
        ax1 = fig.add_subplot(gs[0, 0])

        sizes = [media_refs, tg_citations]
        labels = [f'Media → Telegram\n({media_refs:,} references)',
                 f'Telegram → Media\n({tg_citations:,} citations)']
        colors = ['#3498db', '#e74c3c']
        explode = (0.05, 0.05)

        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors,
               explode=explode, startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
        ax1.set_title('Overall Influence Direction', fontsize=14, fontweight='bold')

        # 2. Top influencing media
        ax2 = fig.add_subplot(gs[0, 1])

        if top_media:
            media_names = [m['name'] for m in top_media]
            media_counts = [m['references'] for m in top_media]

            y_pos = np.arange(len(media_names))
            ax2.barh(y_pos, media_counts, color='#3498db', alpha=0.7)
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(media_names, fontsize=10)
            ax2.set_xlabel('References', fontsize=11, fontweight='bold')
            ax2.set_title('Top 10 Media Influencing Telegram', fontsize=14, fontweight='bold')
            ax2.invert_yaxis()
            ax2.grid(axis='x', alpha=0.3)

            # Add value labels
            for i, count in enumerate(media_counts):
                ax2.text(count + max(media_counts)*0.01, i, f'{count:,}',
                        va='center', fontsize=9)

        # 3. Top channels cited in media
        ax3 = fig.add_subplot(gs[1, 0])

        if top_channels:
            channel_names = [ch['name'][:30] for ch in top_channels]
            channel_counts = [ch['citations'] for ch in top_channels]

            y_pos = np.arange(len(channel_names))
            ax3.barh(y_pos, channel_counts, color='#e74c3c', alpha=0.7)
            ax3.set_yticks(y_pos)
            ax3.set_yticklabels(channel_names, fontsize=10)
            ax3.set_xlabel('Citations', fontsize=11, fontweight='bold')
            ax3.set_title('Top 10 Telegram Channels Cited in Media',
                         fontsize=14, fontweight='bold')
            ax3.invert_yaxis()
            ax3.grid(axis='x', alpha=0.3)

            # Add value labels
            for i, count in enumerate(channel_counts):
                ax3.text(count + max(channel_counts)*0.01, i, f'{count:,}',
                        va='center', fontsize=9)

        # 4. Dominant direction text summary
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis('off')

        dominant = comparison.get('dominant_influence_direction', 'Unknown')

        summary_text = f"""
        INFLUENCE ANALYSIS SUMMARY

        Dominant Direction: {dominant}

        Media → Telegram:
        • Total references: {media_refs:,}
        • Average per message: {media_to_tg.get('average_references_per_message', 0):.3f}
        • Top influencers: {len(top_media)} media sources

        Telegram → Media:
        • Total citations: {tg_citations:,}
        • Channels cited: {tg_to_media.get('channels_cited', 0)}
        • Top cited: {len(top_channels)} channels

        """

        ax4.text(0.1, 0.5, summary_text, transform=ax4.transAxes,
                fontsize=12, verticalalignment='center', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        fig.suptitle('Bidirectional Influence Analysis: Media ↔ Telegram',
                    fontsize=18, fontweight='bold', y=0.98)

        output_file = self.output_dir / "bidirectional_influence.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()

    def create_channel_influence_percentage(self, all_results: Dict):
        """
        Create waterfall-style chart showing influence breakdown by detection method.

        Args:
            all_results: Analysis results for all channels
        """
        # Filter out excluded channels
        all_results = self._filter_channels(all_results)

        # Define traditional media channels
        traditional_media = {
            'Українська правда', 'Суспільне Новини', 'ТСН Новини', 'УНИАН'
        }

        # Prepare data
        independent_data = []
        traditional_data = []

        for channel_name, results in all_results.items():
            stats = results.get('statistics', {})
            breakdown = stats.get('detection_breakdown', {})
            total = stats.get('total_messages', 0)

            if total > 0:
                channel_info = {
                    'Channel': channel_name[:25],
                    'Links': (breakdown.get('link_only', 0) / total) * 100,
                    'Mentions': (breakdown.get('mention_only', 0) / total) * 100,
                    'Similarity': (breakdown.get('similarity_only', 0) / total) * 100,
                    'Multiple': (breakdown.get('multiple_methods', 0) / total) * 100,
                }

                if channel_name in traditional_media:
                    traditional_data.append(channel_info)
                else:
                    independent_data.append(channel_info)

        # Create DataFrames and sort each group
        df_independent = pd.DataFrame(independent_data)
        df_traditional = pd.DataFrame(traditional_data)

        if not df_independent.empty:
            df_independent['Total'] = df_independent['Links'] + df_independent['Mentions'] + df_independent['Similarity'] + df_independent['Multiple']
            df_independent = df_independent.sort_values('Total', ascending=True)

        if not df_traditional.empty:
            df_traditional['Total'] = df_traditional['Links'] + df_traditional['Mentions'] + df_traditional['Similarity'] + df_traditional['Multiple']
            df_traditional = df_traditional.sort_values('Total', ascending=True)

        # Combine with independent first, then traditional
        df = pd.concat([df_independent, df_traditional], ignore_index=True)

        # Create stacked horizontal bar
        fig, ax = plt.subplots(figsize=(14, 10))

        channels = df['Channel']
        links = df['Links']
        mentions = df['Mentions']
        similarity = df['Similarity']
        multiple = df['Multiple']

        y_pos = np.arange(len(channels))

        ax.barh(y_pos, links, label='Links Only', color='#1f77b4')
        ax.barh(y_pos, mentions, left=links, label='Mentions Only', color='#ff7f0e')
        ax.barh(y_pos, similarity, left=links+mentions,
               label='Similarity Only', color='#2ca02c')
        ax.barh(y_pos, multiple, left=links+mentions+similarity,
               label='Multiple Methods', color='#d62728')

        # Add separator line between groups if we have both types
        if not df_independent.empty and not df_traditional.empty:
            separator_pos = len(df_independent) - 0.5
            ax.axhline(y=separator_pos, color='black', linewidth=2, linestyle='--', alpha=0.5)

            # Add section labels
            if len(df_independent) > 0:
                ax.text(-15, len(df_independent) / 2, 'Independent\nChannels',
                       fontsize=11, fontweight='bold', ha='right', va='center',
                       bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

            if len(df_traditional) > 0:
                mid_traditional = len(df_independent) + len(df_traditional) / 2
                ax.text(-15, mid_traditional, 'Traditional\nMedia',
                       fontsize=11, fontweight='bold', ha='right', va='center',
                       bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))

        ax.set_yticks(y_pos)
        ax.set_yticklabels(channels, fontsize=10)
        ax.set_xlabel('Percentage of Messages (%)', fontsize=12, fontweight='bold')
        ax.set_title('Media Influence by Detection Method (% of total messages)',
                     fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='lower right', fontsize=11)
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()

        output_file = self.output_dir / "influence_by_method.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()

    def generate_all_visualizations(self, results_file: Path = None):
        """
        Generate all extended visualizations.

        Args:
            results_file: Path to analysis results JSON (optional)
        """
        if results_file is None:
            results_file = RESULTS_DIR / "analysis_all_channels.json"

        print("\n" + "=" * 80)
        print("GENERATING EXTENDED VISUALIZATIONS")
        print("=" * 80)

        # Load data
        with open(results_file, 'r', encoding='utf-8') as f:
            combined_data = json.load(f)

        # Handle both old and new format
        if "channel_results" in combined_data:
            all_results = combined_data["channel_results"]
            bidirectional_results = combined_data.get("bidirectional_influence")
        else:
            all_results = combined_data
            bidirectional_results = None

        # Generate visualizations
        print("\n📊 Creating extended visualizations...")

        self.create_content_type_heatmap(all_results)
        self.create_top_telegram_channels_chart(all_results)
        self.create_reference_category_breakdown(all_results)
        self.create_media_vs_nonmedia_comparison(all_results)
        self.create_channel_influence_percentage(all_results)

        if bidirectional_results:
            self.create_bidirectional_influence_chart(bidirectional_results)

        print("\n" + "=" * 80)
        print("✅ EXTENDED VISUALIZATIONS COMPLETE")
        print("=" * 80)
        print(f"\n📁 All visualizations saved to: {self.output_dir}")
