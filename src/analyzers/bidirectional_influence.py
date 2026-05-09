"""Bidirectional Influence Analyzer.

Analyzes influence in both directions:
- Media → Telegram: How traditional media influences Telegram channels
- Telegram → Media: How Telegram channels are cited in traditional media
"""
import re
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse


class BidirectionalInfluenceAnalyzer:
    """Analyze bidirectional influence between media and Telegram."""

    # Media domain to name mapping
    MEDIA_DOMAIN_MAP = {
        "suspilne.media": "Суспільне",
        "espreso.tv": "Еспресо",
        "babel.ua": "Бабель",
        "pravda.com.ua": "Українська правда",
        "radiosvoboda.org": "Радіо Свобода",
        "hromadske.ua": "hromadske",
        "zn.ua": "ZN.UA",
        "texty.org.ua": "Тексти",
        "lb.ua": "LB.ua",
        "ukrinform.ua": "Укрінформ",
        "graty.me": "Ґрати",
        "tyzhden.ua": "Український тиждень",
        "rubryka.com": "Рубрика",
        "slovoidilo.ua": "Слово і Діло",
        "novynarnia.com": "Новинарня",
        "frontliner.ua": "Frontliner"
    }

    def __init__(self, time_window_hours: int = 48):
        """
        Initialize the bidirectional influence analyzer.

        Args:
            time_window_hours: Time window for influence analysis (default 48 hours)
        """
        self.time_window_hours = time_window_hours

    def _extract_media_from_url(self, url: str) -> str:
        """
        Extract media name from URL.

        Args:
            url: URL to extract media name from

        Returns:
            Media name or None
        """
        try:
            parsed = urlparse(url.lower())
            domain = parsed.netloc

            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]

            # Look up in domain map
            for domain_key, media_name in self.MEDIA_DOMAIN_MAP.items():
                if domain_key in domain:
                    return media_name

            return None
        except Exception:
            return None

    def analyze_media_to_telegram(
        self, telegram_messages: List[Dict], media_articles: List[Dict]
    ) -> Dict:
        """
        Analyze how media influences Telegram channels.

        Args:
            telegram_messages: List of analyzed Telegram messages
            media_articles: List of media articles

        Returns:
            Dictionary with media influence ranking
        """
        media_influence = {}

        for message in telegram_messages:
            channel_name = message.get('channel_name', 'Unknown')

            # Get all media references
            mentioned_media = set()

            # From links
            link_detection = message.get('link_detection', {})
            if link_detection.get('has_media_link', False):
                for url in link_detection.get('media_urls', []):
                    media_name = self._extract_media_from_url(url)
                    if media_name:
                        mentioned_media.add(media_name)

            # From mentions
            mention_detection = message.get('mention_detection', {})
            if mention_detection.get('has_media_mention', False):
                for media in mention_detection.get('mentioned_media', []):
                    mentioned_media.add(media)

            # From similarity
            similarity_detection = message.get('similarity_detection', {})
            if similarity_detection.get('has_similar_content', False):
                for match in similarity_detection.get('similar_articles', []):
                    media = match.get('media_source')
                    if media:
                        mentioned_media.add(media)

            # Update influence tracking
            for media in mentioned_media:
                if media not in media_influence:
                    media_influence[media] = {
                        'mentions': 0,
                        'links': 0,
                        'similarity_matches': 0,
                        'total_references': 0,
                        'influenced_channels': set()
                    }

                # Increment counters
                if link_detection.get('has_media_link', False):
                    media_influence[media]['links'] += 1
                if mention_detection.get('has_media_mention', False):
                    media_influence[media]['mentions'] += 1
                if similarity_detection.get('has_similar_content', False):
                    media_influence[media]['similarity_matches'] += 1

                media_influence[media]['total_references'] += 1
                media_influence[media]['influenced_channels'].add(channel_name)

        # Convert sets to lists and sort
        media_ranking = []
        for media, stats in media_influence.items():
            stats_copy = stats.copy()
            stats_copy['influenced_channels_count'] = len(stats['influenced_channels'])
            stats_copy['influenced_channels'] = sorted(list(stats['influenced_channels']))
            media_ranking.append((media, stats_copy))

        # Sort by total references
        media_ranking.sort(key=lambda x: x[1]['total_references'], reverse=True)

        return {
            'media_influence_ranking': media_ranking,
            'total_media_sources': len(media_ranking)
        }

    def analyze_telegram_to_media(
        self, telegram_messages: List[Dict], media_articles: List[Dict]
    ) -> Dict:
        """
        Analyze how Telegram channels are cited in media.

        Args:
            telegram_messages: List of analyzed Telegram messages
            media_articles: List of media articles

        Returns:
            Dictionary with channel influence ranking
        """
        # Get list of unique channel names from messages
        channel_names = set()
        for message in telegram_messages:
            channel_name = message.get('channel_name')
            if channel_name:
                channel_names.add(channel_name)

        # Track which channels are cited in which media
        channel_influence = {}

        for article in media_articles:
            text = article.get('text', '') or ''
            title = article.get('title', '') or ''
            full_text = f"{title} {text}".lower()
            media_source = article.get('source', 'Unknown')

            # Check if any channel is mentioned in the article
            for channel_name in channel_names:
                # Check for channel mentions (case-insensitive)
                if channel_name.lower() in full_text:
                    if channel_name not in channel_influence:
                        channel_influence[channel_name] = {
                            'cited_in_media': 0,
                            'unique_media': set(),
                            'media_list': []
                        }

                    channel_influence[channel_name]['cited_in_media'] += 1
                    channel_influence[channel_name]['unique_media'].add(media_source)

                # Also check for @mentions and t.me/ links
                at_mention = f"@{channel_name.lower().replace(' ', '')}"
                tme_mention = f"t.me/{channel_name.lower().replace(' ', '')}"

                if at_mention in full_text or tme_mention in full_text:
                    if channel_name not in channel_influence:
                        channel_influence[channel_name] = {
                            'cited_in_media': 0,
                            'unique_media': set(),
                            'media_list': []
                        }

                    channel_influence[channel_name]['cited_in_media'] += 1
                    channel_influence[channel_name]['unique_media'].add(media_source)

        # Convert sets to lists and sort
        channel_ranking = []
        for channel, stats in channel_influence.items():
            stats_copy = stats.copy()
            stats_copy['unique_media_influenced'] = len(stats['unique_media'])
            stats_copy['media_list'] = sorted(list(stats['unique_media']))
            del stats_copy['unique_media']
            channel_ranking.append((channel, stats_copy))

        # Sort by citation count
        channel_ranking.sort(key=lambda x: x[1]['cited_in_media'], reverse=True)

        return {
            'channel_influence_ranking': channel_ranking,
            'total_channels_influencing_media': len(channel_ranking)
        }

    def compare_influence_directions(
        self, media_to_tg: Dict, tg_to_media: Dict, total_tg_messages: int
    ) -> Dict:
        """
        Compare influence in both directions and determine dominant direction.

        Args:
            media_to_tg: Media to Telegram analysis results
            tg_to_media: Telegram to Media analysis results
            total_tg_messages: Total number of Telegram messages

        Returns:
            Dictionary with comparison results
        """
        # Media → Telegram strength
        media_to_tg_references = sum(
            stats['total_references']
            for _, stats in media_to_tg['media_influence_ranking']
        )
        media_to_tg_avg = (
            media_to_tg_references / total_tg_messages
            if total_tg_messages > 0 else 0
        )

        # Telegram → Media strength
        tg_to_media_citations = sum(
            stats['cited_in_media']
            for _, stats in tg_to_media['channel_influence_ranking']
        )
        tg_to_media_channels = tg_to_media['total_channels_influencing_media']

        # Determine dominant direction
        if media_to_tg_references > tg_to_media_citations:
            dominant_direction = "Media -> Telegram"
        elif tg_to_media_citations > media_to_tg_references:
            dominant_direction = "Telegram -> Media"
        else:
            dominant_direction = "Balanced"

        # Get top 5 influencers in each direction
        top_media = [
            {"name": name, "references": stats['total_references']}
            for name, stats in media_to_tg['media_influence_ranking'][:5]
        ]

        top_channels = [
            {"name": name, "citations": stats['cited_in_media']}
            for name, stats in tg_to_media['channel_influence_ranking'][:5]
        ]

        return {
            'media_to_telegram': {
                'total_references': media_to_tg_references,
                'average_references_per_message': media_to_tg_avg,
                'top_influencers': top_media
            },
            'telegram_to_media': {
                'total_citations': tg_to_media_citations,
                'channels_cited': tg_to_media_channels,
                'top_influencers': top_channels
            },
            'dominant_influence_direction': dominant_direction,
            'influence_ratio': {
                'media_to_telegram_strength': media_to_tg_references,
                'telegram_to_media_strength': tg_to_media_citations
            }
        }

    def generate_full_analysis(
        self, telegram_messages: List[Dict], media_articles: List[Dict]
    ) -> Dict:
        """
        Generate complete bidirectional influence analysis.

        Args:
            telegram_messages: List of analyzed Telegram messages
            media_articles: List of media articles

        Returns:
            Complete analysis dictionary
        """
        # Analyze both directions
        media_to_tg = self.analyze_media_to_telegram(telegram_messages, media_articles)
        tg_to_media = self.analyze_telegram_to_media(telegram_messages, media_articles)

        # Compare directions
        comparison = self.compare_influence_directions(
            media_to_tg, tg_to_media, len(telegram_messages)
        )

        return {
            'media_to_telegram': media_to_tg,
            'telegram_to_media': tg_to_media,
            'comparison': comparison,
            'analysis_metadata': {
                'total_telegram_messages': len(telegram_messages),
                'total_media_articles': len(media_articles),
                'time_window_hours': self.time_window_hours
            }
        }
