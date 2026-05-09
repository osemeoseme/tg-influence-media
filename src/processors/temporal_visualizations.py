"""Temporal visualizations showing how data changes over time.

Creates time-series visualizations:
- Media influence trends over time
- Content type evolution
- Message volume patterns
- Reference behavior changes
- Daily/weekly/monthly patterns
"""
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List

from src.utils.config import RESULTS_DIR


class TemporalVisualizer:
    """Create temporal visualizations showing changes over time."""

    def __init__(self):
        """Initialize the temporal visualizer."""
        sns.set_style("whitegrid")
        sns.set_palette("husl")
        self.output_dir = RESULTS_DIR / "temporal"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse_date(self, date_str):
        """Parse date string to datetime object."""
        if isinstance(date_str, datetime):
            return date_str

        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                # Try alternative formats
                return pd.to_datetime(date_str)
            except:
                return None

    def create_media_influence_timeline(self, all_results: Dict):
        """
        Create timeline showing media influence percentage over time.

        Args:
            all_results: Analysis results for all channels
        """
        print("\n📈 Creating media influence timeline...")

        # Collect all messages with dates
        timeline_data = []

        for channel_name, results in all_results.items():
            for msg in results.get('messages', []):
                date = self.parse_date(msg.get('date'))
                if not date:
                    continue

                # Check if influenced by media
                has_link = msg.get('link_detection', {}).get('has_media_link', False)
                has_mention = msg.get('mention_detection', {}).get('has_media_mention', False)
                has_similarity = msg.get('similarity_detection', {}).get('has_similar_content', False)

                influenced = has_link or has_mention or has_similarity

                timeline_data.append({
                    'date': date.date(),
                    'channel': channel_name,
                    'influenced': 1 if influenced else 0
                })

        if not timeline_data:
            print("⚠️  No temporal data available")
            return

        df = pd.DataFrame(timeline_data)

        # Group by date and calculate influence percentage
        daily_stats = df.groupby('date').agg({
            'influenced': ['sum', 'count']
        }).reset_index()
        daily_stats.columns = ['date', 'influenced', 'total']
        daily_stats['percentage'] = (daily_stats['influenced'] / daily_stats['total']) * 100

        # Create 7-day rolling average
        daily_stats['rolling_avg'] = daily_stats['percentage'].rolling(window=7, min_periods=1).mean()

        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True)

        # Plot 1: Message volume
        ax1.fill_between(daily_stats['date'], daily_stats['total'], alpha=0.3, color='steelblue')
        ax1.plot(daily_stats['date'], daily_stats['total'], color='steelblue', linewidth=1.5)
        ax1.set_ylabel('Messages per Day', fontsize=12, fontweight='bold')
        ax1.set_title('Daily Message Volume', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)

        # Plot 2: Influence percentage
        ax2.plot(daily_stats['date'], daily_stats['percentage'],
                color='lightgray', alpha=0.5, linewidth=1, label='Daily')
        ax2.plot(daily_stats['date'], daily_stats['rolling_avg'],
                color='#e74c3c', linewidth=2.5, label='7-day Average')
        ax2.fill_between(daily_stats['date'], daily_stats['rolling_avg'],
                         alpha=0.3, color='#e74c3c')
        ax2.set_ylabel('Media Influence (%)', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax2.set_title('Media Influence Percentage Over Time', fontsize=14, fontweight='bold')
        ax2.legend(loc='best', fontsize=10)
        ax2.grid(True, alpha=0.3)

        # Format x-axis
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.xticks(rotation=45)

        fig.suptitle('Temporal Analysis: Message Volume & Media Influence',
                    fontsize=16, fontweight='bold', y=0.995)

        plt.tight_layout()

        output_file = self.output_dir / "media_influence_timeline.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()

    def create_content_type_evolution(self, all_results: Dict):
        """
        Create stacked area chart showing content type evolution over time.

        Args:
            all_results: Analysis results for all channels
        """
        print("\n📊 Creating content type evolution chart...")

        # Collect messages with content types
        timeline_data = []

        for channel_name, results in all_results.items():
            for msg in results.get('messages', []):
                date = self.parse_date(msg.get('date'))
                if not date:
                    continue

                content_types = msg.get('content_type_detection', {}).get('content_types', ['news'])

                for ct in content_types:
                    timeline_data.append({
                        'date': date.date(),
                        'content_type': ct
                    })

        if not timeline_data:
            print("⚠️  No content type temporal data available")
            return

        df = pd.DataFrame(timeline_data)

        # Group by week for smoother visualization
        df['week'] = pd.to_datetime(df['date']) - pd.to_timedelta(pd.to_datetime(df['date']).dt.dayofweek, unit='d')

        # Pivot to get content types as columns
        weekly_counts = df.groupby(['week', 'content_type']).size().unstack(fill_value=0)

        # Calculate percentages
        weekly_pct = weekly_counts.div(weekly_counts.sum(axis=1), axis=0) * 100

        # Create stacked area chart
        fig, ax = plt.subplots(figsize=(16, 8))

        weekly_pct.plot.area(ax=ax, alpha=0.7, linewidth=2)

        ax.set_ylabel('Percentage of Messages (%)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Date (Weekly)', fontsize=12, fontweight='bold')
        ax.set_title('Content Type Evolution Over Time', fontsize=16, fontweight='bold', pad=20)
        ax.legend(title='Content Type', loc='upper left', bbox_to_anchor=(1, 1), fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45)

        plt.tight_layout()

        output_file = self.output_dir / "content_type_evolution.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()

    def create_channel_activity_heatmap(self, all_results: Dict):
        """
        Create heatmap showing channel activity by day of week and hour.

        Args:
            all_results: Analysis results for all channels
        """
        print("\n🔥 Creating channel activity heatmap...")

        # Collect message timestamps
        timeline_data = []

        for channel_name, results in all_results.items():
            for msg in results.get('messages', []):
                date = self.parse_date(msg.get('date'))
                if not date:
                    continue

                timeline_data.append({
                    'channel': channel_name,
                    'hour': date.hour,
                    'day_of_week': date.strftime('%A'),
                    'day_num': date.weekday()
                })

        if not timeline_data:
            print("⚠️  No timestamp data available")
            return

        df = pd.DataFrame(timeline_data)

        # Create pivot table
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        heatmap_data = df.groupby(['day_of_week', 'hour']).size().unstack(fill_value=0)
        heatmap_data = heatmap_data.reindex(day_order)

        # Create heatmap
        fig, ax = plt.subplots(figsize=(16, 8))

        sns.heatmap(heatmap_data, cmap='YlOrRd', annot=False, fmt='d',
                   cbar_kws={'label': 'Number of Messages'}, ax=ax)

        ax.set_ylabel('Day of Week', fontsize=12, fontweight='bold')
        ax.set_xlabel('Hour of Day', fontsize=12, fontweight='bold')
        ax.set_title('Channel Activity Heatmap (Day of Week × Hour)',
                    fontsize=16, fontweight='bold', pad=20)

        plt.tight_layout()

        output_file = self.output_dir / "activity_heatmap.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()

    def create_top_media_trends(self, all_results: Dict, top_n: int = 8):
        """
        Create line chart showing mentions of top media sources over time.

        Args:
            all_results: Analysis results for all channels
            top_n: Number of top media sources to track
        """
        print(f"\n📰 Creating top {top_n} media trends chart...")

        # First, find top media sources overall
        media_total = Counter()

        for channel_name, results in all_results.items():
            for msg in results.get('messages', []):
                # Get mentioned media
                mentioned = msg.get('mention_detection', {}).get('mentioned_media', [])
                media_total.update(mentioned)

        top_media = [media for media, _ in media_total.most_common(top_n)]

        if not top_media:
            print("⚠️  No media mentions found")
            return

        # Collect timeline data for top media
        timeline_data = []

        for channel_name, results in all_results.items():
            for msg in results.get('messages', []):
                date = self.parse_date(msg.get('date'))
                if not date:
                    continue

                mentioned = msg.get('mention_detection', {}).get('mentioned_media', [])

                for media in mentioned:
                    if media in top_media:
                        timeline_data.append({
                            'date': date.date(),
                            'media': media
                        })

        if not timeline_data:
            print("⚠️  No temporal media data available")
            return

        df = pd.DataFrame(timeline_data)

        # Group by week for smoother lines
        df['week'] = pd.to_datetime(df['date']) - pd.to_timedelta(pd.to_datetime(df['date']).dt.dayofweek, unit='d')

        weekly_counts = df.groupby(['week', 'media']).size().unstack(fill_value=0)

        # Apply rolling average
        weekly_smooth = weekly_counts.rolling(window=4, min_periods=1).mean()

        # Create line chart
        fig, ax = plt.subplots(figsize=(16, 8))

        for media in top_media:
            if media in weekly_smooth.columns:
                ax.plot(weekly_smooth.index, weekly_smooth[media],
                       linewidth=2.5, label=media, marker='o', markersize=4, alpha=0.8)

        ax.set_ylabel('Mentions per Week (4-week avg)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_title(f'Top {top_n} Media Sources: Mention Trends Over Time',
                    fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45)

        plt.tight_layout()

        output_file = self.output_dir / "top_media_trends.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()

    def create_channel_comparison_timeline(self, all_results: Dict):
        """
        Create timeline comparing activity across different channels.

        Args:
            all_results: Analysis results for all channels
        """
        print("\n📱 Creating channel comparison timeline...")

        # Collect data per channel
        timeline_data = []

        for channel_name, results in all_results.items():
            for msg in results.get('messages', []):
                date = self.parse_date(msg.get('date'))
                if not date:
                    continue

                timeline_data.append({
                    'date': date.date(),
                    'channel': channel_name[:25]
                })

        if not timeline_data:
            print("⚠️  No temporal channel data available")
            return

        df = pd.DataFrame(timeline_data)

        # Group by month for clarity
        df['month'] = pd.to_datetime(df['date']).dt.to_period('M')

        monthly_counts = df.groupby(['month', 'channel']).size().unstack(fill_value=0)
        monthly_counts.index = monthly_counts.index.to_timestamp()

        # Create stacked area chart
        fig, ax = plt.subplots(figsize=(16, 8))

        monthly_counts.plot.area(ax=ax, alpha=0.7, linewidth=1.5)

        ax.set_ylabel('Messages per Month', fontsize=12, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_title('Channel Activity Comparison Over Time',
                    fontsize=16, fontweight='bold', pad=20)
        ax.legend(title='Channel', loc='upper left', bbox_to_anchor=(1, 1), fontsize=9)
        ax.grid(True, alpha=0.3)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45)

        plt.tight_layout()

        output_file = self.output_dir / "channel_comparison_timeline.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()

    def create_detection_method_timeline(self, all_results: Dict):
        """
        Create timeline showing how detection methods perform over time.

        Args:
            all_results: Analysis results for all channels
        """
        print("\n🔍 Creating detection method timeline...")

        # Collect detection data
        timeline_data = []

        for channel_name, results in all_results.items():
            for msg in results.get('messages', []):
                date = self.parse_date(msg.get('date'))
                if not date:
                    continue

                has_link = msg.get('link_detection', {}).get('has_media_link', False)
                has_mention = msg.get('mention_detection', {}).get('has_media_mention', False)
                has_similarity = msg.get('similarity_detection', {}).get('has_similar_content', False)

                if has_link:
                    timeline_data.append({'date': date.date(), 'method': 'Links'})
                if has_mention:
                    timeline_data.append({'date': date.date(), 'method': 'Mentions'})
                if has_similarity:
                    timeline_data.append({'date': date.date(), 'method': 'Similarity'})

        if not timeline_data:
            print("⚠️  No detection method temporal data available")
            return

        df = pd.DataFrame(timeline_data)

        # Group by week
        df['week'] = pd.to_datetime(df['date']) - pd.to_timedelta(pd.to_datetime(df['date']).dt.dayofweek, unit='d')

        weekly_counts = df.groupby(['week', 'method']).size().unstack(fill_value=0)

        # Apply rolling average
        weekly_smooth = weekly_counts.rolling(window=4, min_periods=1).mean()

        # Create line chart
        fig, ax = plt.subplots(figsize=(16, 8))

        colors = {'Links': '#1f77b4', 'Mentions': '#ff7f0e', 'Similarity': '#2ca02c'}

        for method in ['Links', 'Mentions', 'Similarity']:
            if method in weekly_smooth.columns:
                ax.plot(weekly_smooth.index, weekly_smooth[method],
                       linewidth=2.5, label=method, color=colors[method],
                       marker='o', markersize=4, alpha=0.8)
                ax.fill_between(weekly_smooth.index, weekly_smooth[method],
                               alpha=0.2, color=colors[method])

        ax.set_ylabel('Detections per Week (4-week avg)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_title('Detection Method Performance Over Time',
                    fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='best', fontsize=11)
        ax.grid(True, alpha=0.3)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=45)

        plt.tight_layout()

        output_file = self.output_dir / "detection_method_timeline.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_file}")
        plt.close()

    def generate_all_visualizations(self, results_file: Path = None):
        """
        Generate all temporal visualizations.

        Args:
            results_file: Path to analysis results JSON (optional)
        """
        if results_file is None:
            results_file = RESULTS_DIR / "analysis_all_channels.json"

        print("\n" + "=" * 80)
        print("GENERATING TEMPORAL VISUALIZATIONS")
        print("=" * 80)

        # Load data
        with open(results_file, 'r', encoding='utf-8') as f:
            combined_data = json.load(f)

        # Handle both old and new format
        if "channel_results" in combined_data:
            all_results = combined_data["channel_results"]
        else:
            all_results = combined_data

        # Generate visualizations
        print("\n⏰ Creating time-series visualizations...")

        self.create_media_influence_timeline(all_results)
        self.create_content_type_evolution(all_results)
        self.create_channel_activity_heatmap(all_results)
        self.create_top_media_trends(all_results)
        self.create_channel_comparison_timeline(all_results)
        self.create_detection_method_timeline(all_results)

        print("\n" + "=" * 80)
        print("✅ TEMPORAL VISUALIZATIONS COMPLETE")
        print("=" * 80)
        print(f"\n📁 All visualizations saved to: {self.output_dir}")
