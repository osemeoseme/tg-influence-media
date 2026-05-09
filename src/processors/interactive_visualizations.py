"""Interactive Visualizations using Plotly.

Creates interactive HTML visualizations for influence analysis:
- Influence network graph
- Media ranking chart
- Channel comparison chart
- Content type distribution
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
from typing import Dict, List
from pathlib import Path

from src.utils.config import RESULTS_DIR


class InteractiveVisualizer:
    """Create interactive Plotly visualizations."""

    # Color scheme
    COLORS = {
        'media': '#1f77b4',  # Blue
        'telegram': '#ff7f0e',  # Orange
        'link': '#2ca02c',  # Green
        'mention': '#d62728',  # Red
        'similarity': '#9467bd'  # Purple
    }

    def __init__(self):
        """Initialize the interactive visualizer."""
        self.output_dir = RESULTS_DIR / "interactive"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_influence_network(
        self, all_results: Dict, bidirectional_analysis: Dict = None
    ) -> go.Figure:
        """
        Create interactive network graph showing Media-Telegram influence.

        Args:
            all_results: Analysis results for all channels
            bidirectional_analysis: Bidirectional analysis results

        Returns:
            Plotly Figure object
        """
        # Create directed graph
        G = nx.DiGraph()

        # Add nodes and edges from media to telegram
        for channel_name, results in all_results.items():
            # Add telegram channel node
            G.add_node(channel_name, node_type='telegram')

            # Get media influence stats
            stats = results.get('statistics', {})
            by_method = stats.get('by_method', {})

            # From link detection
            link_counts = by_method.get('links', {}).get('link_counts_by_media', {})
            for media, count in link_counts.items():
                G.add_node(media, node_type='media')
                if G.has_edge(media, channel_name):
                    G[media][channel_name]['weight'] += count
                else:
                    G.add_edge(media, channel_name, weight=count)

            # From mention detection
            mention_counts = by_method.get('mentions', {}).get('mention_counts_by_media', {})
            for media, count in mention_counts.items():
                G.add_node(media, node_type='media')
                if G.has_edge(media, channel_name):
                    G[media][channel_name]['weight'] += count
                else:
                    G.add_edge(media, channel_name, weight=count)

        # Generate layout
        pos = nx.spring_layout(G, k=2, iterations=50)

        # Create edge traces
        edge_x = []
        edge_y = []
        edge_weights = []

        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_weights.append(edge[2].get('weight', 1))

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color=self.COLORS['link']),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        )

        # Create node traces (separate for media and telegram)
        media_node_x = []
        media_node_y = []
        media_node_text = []
        media_node_size = []

        telegram_node_x = []
        telegram_node_y = []
        telegram_node_text = []
        telegram_node_size = []

        for node in G.nodes(data=True):
            x, y = pos[node[0]]
            node_type = node[1].get('node_type', 'unknown')

            # Calculate node size based on degree
            degree = G.degree(node[0])
            size = 10 + degree * 2

            if node_type == 'media':
                media_node_x.append(x)
                media_node_y.append(y)
                media_node_text.append(node[0])
                media_node_size.append(size)
            else:
                telegram_node_x.append(x)
                telegram_node_y.append(y)
                telegram_node_text.append(node[0])
                telegram_node_size.append(size)

        # Media nodes (squares)
        media_trace = go.Scatter(
            x=media_node_x, y=media_node_y,
            mode='markers+text',
            marker=dict(
                size=media_node_size,
                color=self.COLORS['media'],
                symbol='square',
                line=dict(width=2, color='white')
            ),
            text=media_node_text,
            textposition="top center",
            textfont=dict(size=10),
            hoverinfo='text',
            hovertext=media_node_text,
            name='Media',
            showlegend=True
        )

        # Telegram nodes (circles)
        telegram_trace = go.Scatter(
            x=telegram_node_x, y=telegram_node_y,
            mode='markers+text',
            marker=dict(
                size=telegram_node_size,
                color=self.COLORS['telegram'],
                symbol='circle',
                line=dict(width=2, color='white')
            ),
            text=telegram_node_text,
            textposition="top center",
            textfont=dict(size=10),
            hoverinfo='text',
            hovertext=telegram_node_text,
            name='Telegram',
            showlegend=True
        )

        # Create figure
        fig = go.Figure(
            data=[edge_trace, media_trace, telegram_trace],
            layout=go.Layout(
                title=dict(text='Media-Telegram Influence Network', font=dict(size=16)),
                showlegend=True,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white',
                height=700
            )
        )

        # Save
        output_file = self.output_dir / "influence_network.html"
        fig.write_html(str(output_file))
        print(f"   Saved: {output_file}")

        return fig

    def create_media_influence_ranking(self, all_results: Dict) -> go.Figure:
        """
        Create horizontal bar chart of media mentions.

        Args:
            all_results: Analysis results for all channels

        Returns:
            Plotly Figure object
        """
        # Aggregate media mentions across all channels
        media_mentions = {}

        for channel_name, results in all_results.items():
            stats = results.get('statistics', {})
            by_method = stats.get('by_method', {})

            # From links
            link_counts = by_method.get('links', {}).get('link_counts_by_media', {})
            for media, count in link_counts.items():
                media_mentions[media] = media_mentions.get(media, 0) + count

            # From mentions
            mention_counts = by_method.get('mentions', {}).get('mention_counts_by_media', {})
            for media, count in mention_counts.items():
                media_mentions[media] = media_mentions.get(media, 0) + count

        # Sort by count
        sorted_media = sorted(media_mentions.items(), key=lambda x: x[1], reverse=True)
        media_names = [m[0] for m in sorted_media]
        counts = [m[1] for m in sorted_media]

        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                y=media_names,
                x=counts,
                orientation='h',
                marker=dict(
                    color=counts,
                    colorscale='Blues',
                    showscale=True,
                    colorbar=dict(title="Mentions")
                ),
                hovertemplate='<b>%{y}</b><br>Mentions: %{x}<extra></extra>'
            )
        ])

        fig.update_layout(
            title='Media Influence Ranking',
            xaxis_title='Total Mentions',
            yaxis_title='Media Source',
            height=max(400, len(media_names) * 25),
            plot_bgcolor='white',
            yaxis=dict(autorange='reversed')
        )

        # Save
        output_file = self.output_dir / "media_ranking.html"
        fig.write_html(str(output_file))
        print(f"   Saved: {output_file}")

        return fig

    def create_channel_comparison(self, all_results: Dict) -> go.Figure:
        """
        Create side-by-side comparison of channels.

        Args:
            all_results: Analysis results for all channels

        Returns:
            Plotly Figure object
        """
        # Extract data
        channel_names = []
        total_messages = []
        influence_percentages = []

        for channel_name, results in all_results.items():
            stats = results.get('statistics', {})
            channel_names.append(channel_name)
            total_messages.append(stats.get('total_messages', 0))
            influence_percentages.append(stats.get('percentage_influenced', 0))

        # Create subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Total Messages', 'Influence Percentage'),
            horizontal_spacing=0.15
        )

        # Total messages bar chart
        fig.add_trace(
            go.Bar(
                x=channel_names,
                y=total_messages,
                marker_color=self.COLORS['telegram'],
                name='Messages',
                hovertemplate='<b>%{x}</b><br>Messages: %{y}<extra></extra>'
            ),
            row=1, col=1
        )

        # Influence percentage bar chart with color scale
        fig.add_trace(
            go.Bar(
                x=channel_names,
                y=influence_percentages,
                marker=dict(
                    color=influence_percentages,
                    colorscale='Oranges',
                    showscale=True,
                    colorbar=dict(title="Influence %", x=1.15)
                ),
                name='Influence %',
                hovertemplate='<b>%{x}</b><br>Influence: %{y:.1f}%<extra></extra>'
            ),
            row=1, col=2
        )

        fig.update_xaxes(title_text="Channel", row=1, col=1)
        fig.update_xaxes(title_text="Channel", row=1, col=2)
        fig.update_yaxes(title_text="Count", row=1, col=1)
        fig.update_yaxes(title_text="Percentage", row=1, col=2)

        fig.update_layout(
            title_text='Channel Comparison',
            showlegend=False,
            height=500,
            plot_bgcolor='white'
        )

        # Save
        output_file = self.output_dir / "channel_comparison.html"
        fig.write_html(str(output_file))
        print(f"   Saved: {output_file}")

        return fig

    def create_content_type_distribution(self, all_results: Dict) -> go.Figure:
        """
        Create donut chart showing content type distribution.

        Args:
            all_results: Analysis results for all channels

        Returns:
            Plotly Figure object
        """
        # Aggregate content types
        content_type_counts = {}

        for channel_name, results in all_results.items():
            stats = results.get('statistics', {})
            content_types = stats.get('content_types', {})
            counts = content_types.get('content_type_counts', {})

            for ct, count in counts.items():
                content_type_counts[ct] = content_type_counts.get(ct, 0) + count

        # Create pie chart
        labels = list(content_type_counts.keys())
        values = list(content_type_counts.values())

        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )
        ])

        fig.update_layout(
            title='Content Type Distribution',
            height=500,
            plot_bgcolor='white'
        )

        # Save
        output_file = self.output_dir / "content_types.html"
        fig.write_html(str(output_file))
        print(f"   Saved: {output_file}")

        return fig

    def save_all_visualizations(
        self, all_results: Dict, bidirectional_analysis: Dict = None
    ):
        """
        Generate and save all visualizations.

        Args:
            all_results: Analysis results for all channels
            bidirectional_analysis: Bidirectional analysis results
        """
        print("\nGenerating interactive visualizations...")

        # Create all visualizations
        self.create_influence_network(all_results, bidirectional_analysis)
        self.create_media_influence_ranking(all_results)
        self.create_channel_comparison(all_results)
        self.create_content_type_distribution(all_results)

        print(f"\nAll visualizations saved to: {self.output_dir}")
