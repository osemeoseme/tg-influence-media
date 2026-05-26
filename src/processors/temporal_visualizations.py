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

    # Channels with insufficient data (redirects to private channels)
    EXCLUDED_CHANNELS = [
        'Україна 24/7 - новини',
        'Інсайдер ЗСУ'
    ]

    def __init__(self):
        """Initialize the temporal visualizer."""
        sns.set_style("whitegrid")
        sns.set_palette("husl")
        self.output_dir = RESULTS_DIR / "temporal"
        self.output_dir.mkdir(parents=True, exist_ok=True)

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

        # Filter out excluded channels
        all_results = self._filter_channels(all_results)

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

        # Create 7-day rolling averages
        daily_stats['rolling_avg_pct'] = daily_stats['percentage'].rolling(window=7, min_periods=1).mean()
        daily_stats['rolling_avg_volume'] = daily_stats['total'].rolling(window=7, min_periods=1).mean()

        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True)

        # Plot 1: Message volume with rolling average
        ax1.plot(daily_stats['date'], daily_stats['total'],
                color='lightsteelblue', alpha=0.4, linewidth=1, label='Daily')
        ax1.plot(daily_stats['date'], daily_stats['rolling_avg_volume'],
                color='steelblue', linewidth=2.5, label='7-day Average')
        ax1.fill_between(daily_stats['date'], daily_stats['rolling_avg_volume'],
                         alpha=0.3, color='steelblue')
        ax1.set_ylabel('Messages per Day', fontsize=12, fontweight='bold')
        ax1.set_title('Daily Message Volume', fontsize=14, fontweight='bold')
        ax1.legend(loc='best', fontsize=10)
        ax1.grid(True, alpha=0.3)

        # Plot 2: Influence percentage
        ax2.plot(daily_stats['date'], daily_stats['percentage'],
                color='lightgray', alpha=0.5, linewidth=1, label='Daily')
        ax2.plot(daily_stats['date'], daily_stats['rolling_avg_pct'],
                color='#e74c3c', linewidth=2.5, label='7-day Average')
        ax2.fill_between(daily_stats['date'], daily_stats['rolling_avg_pct'],
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

        # Filter out excluded channels
        all_results = self._filter_channels(all_results)

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

        # Convert to datetime and group by week for smoother visualization
        df['datetime'] = pd.to_datetime(df['date'])
        df['week'] = df['datetime'] - pd.to_timedelta(df['datetime'].dt.dayofweek, unit='d')

        # Pivot to get content types as columns
        weekly_counts = df.groupby(['week', 'content_type']).size().unstack(fill_value=0)

        # Calculate percentages
        weekly_pct = weekly_counts.div(weekly_counts.sum(axis=1), axis=0) * 100

        # Create stacked area chart
        fig, ax = plt.subplots(figsize=(16, 8))

        # Ensure index is proper datetime - reset and convert explicitly
        weekly_pct = weekly_pct.reset_index()
        weekly_pct['week'] = pd.to_datetime(weekly_pct['week'])
        weekly_pct = weekly_pct.set_index('week')

        weekly_pct.plot.area(ax=ax, alpha=0.7, linewidth=2)

        ax.set_ylabel('Percentage of Messages (%)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Date (Weekly)', fontsize=12, fontweight='bold')
        ax.set_title('Content Type Evolution Over Time', fontsize=16, fontweight='bold', pad=20)
        ax.legend(title='Content Type', loc='upper left', bbox_to_anchor=(1, 1), fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)

        # Format x-axis with proper date formatting
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

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

        # Filter out excluded channels
        all_results = self._filter_channels(all_results)

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

        # Filter out excluded channels
        all_results = self._filter_channels(all_results)

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
        df['datetime'] = pd.to_datetime(df['date'])
        df['week'] = df['datetime'] - pd.to_timedelta(df['datetime'].dt.dayofweek, unit='d')

        weekly_counts = df.groupby(['week', 'media']).size().unstack(fill_value=0)

        # Ensure index is proper datetime
        weekly_counts.index = pd.to_datetime(weekly_counts.index)

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

        # Filter out excluded channels
        all_results = self._filter_channels(all_results)

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
        df['datetime'] = pd.to_datetime(df['date'])
        df['month'] = df['datetime'].dt.to_period('M')

        monthly_counts = df.groupby(['month', 'channel']).size().unstack(fill_value=0)
        monthly_counts.index = pd.to_datetime(monthly_counts.index.to_timestamp())

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

        # Filter out excluded channels
        all_results = self._filter_channels(all_results)

        # Collect detection data and total messages
        timeline_data = []
        total_messages_data = []

        for channel_name, results in all_results.items():
            for msg in results.get('messages', []):
                date = self.parse_date(msg.get('date'))
                if not date:
                    continue

                # Track total messages
                total_messages_data.append({'date': date.date()})

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
        df_total = pd.DataFrame(total_messages_data)

        # Group by week
        df['datetime'] = pd.to_datetime(df['date'])
        df_total['datetime'] = pd.to_datetime(df_total['date'])
        df['week'] = df['datetime'] - pd.to_timedelta(df['datetime'].dt.dayofweek, unit='d')
        df_total['week'] = df_total['datetime'] - pd.to_timedelta(df_total['datetime'].dt.dayofweek, unit='d')

        weekly_counts = df.groupby(['week', 'method']).size().unstack(fill_value=0)
        weekly_total = df_total.groupby('week').size()

        # Ensure index is proper datetime
        weekly_counts.index = pd.to_datetime(weekly_counts.index)
        weekly_total.index = pd.to_datetime(weekly_total.index)

        # Calculate percentages
        weekly_percentages = weekly_counts.div(weekly_total, axis=0) * 100

        # Apply rolling average
        weekly_smooth = weekly_percentages.rolling(window=4, min_periods=1).mean()

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

        ax.set_ylabel('Detection Rate (% of messages, 4-week avg)', fontsize=12, fontweight='bold')
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

    def create_message_volume_timeline(self, all_results: Dict):
        """
        Create timeline showing total message volume over time from 2020.

        Args:
            all_results: Analysis results for all channels
        """
        print("\n📊 Creating message volume timeline from 2020...")

        # Filter out excluded channels
        all_results = self._filter_channels(all_results)

        # Collect all messages with dates
        message_dates = []

        for channel_name, results in all_results.items():
            for msg in results.get('messages', []):
                date = self.parse_date(msg.get('date'))
                if not date:
                    continue

                message_dates.append({
                    'date': date,
                    'channel': channel_name
                })

        if not message_dates:
            print("⚠️  No temporal data available")
            return

        df = pd.DataFrame(message_dates)

        # Filter to 2020 onwards (make timezone-aware for comparison)
        cutoff_date = pd.Timestamp('2020-01-01', tz='UTC')
        df = df[df['date'] >= cutoff_date]

        if df.empty:
            print("⚠️  No data from 2020 onwards")
            return

        # Aggregate by month
        df['year_month'] = df['date'].dt.to_period('M').dt.to_timestamp()
        monthly_counts = df.groupby('year_month').size().reset_index(name='message_count')

        # Calculate rolling 3-month average
        monthly_counts['rolling_avg'] = monthly_counts['message_count'].rolling(window=3, min_periods=1).mean()

        # Create figure
        fig, ax = plt.subplots(figsize=(16, 7))

        # Plot bars for monthly counts
        ax.bar(monthly_counts['year_month'], monthly_counts['message_count'],
               width=20, alpha=0.6, color='steelblue', label='Monthly Messages')

        # Plot rolling average line
        ax.plot(monthly_counts['year_month'], monthly_counts['rolling_avg'],
                color='darkred', linewidth=3, label='3-Month Average',
                marker='o', markersize=5)

        # Formatting
        ax.set_xlabel('Date', fontsize=13, fontweight='bold')
        ax.set_ylabel('Number of Messages', fontsize=13, fontweight='bold')
        ax.set_title('Message Volume Over Time (2020 - Present)',
                    fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='best', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.xticks(rotation=45, ha='right')

        # Add summary statistics
        total_messages = monthly_counts['message_count'].sum()
        avg_monthly = monthly_counts['message_count'].mean()
        max_month = monthly_counts.loc[monthly_counts['message_count'].idxmax()]

        stats_text = f'Total: {total_messages:,} messages\n'
        stats_text += f'Avg/month: {avg_monthly:,.0f}\n'
        stats_text += f'Peak: {max_month["message_count"]:,.0f} ({max_month["year_month"].strftime("%b %Y")})'

        ax.text(0.02, 0.98, stats_text,
               transform=ax.transAxes,
               fontsize=11,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        plt.tight_layout()

        output_file = self.output_dir / "message_volume_timeline.png"
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

        self.create_message_volume_timeline(all_results)
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
