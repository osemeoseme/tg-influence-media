"""Reference Detector for non-media references in Telegram messages.

Detects what Telegram posts reference when they don't cite traditional media:
- Social media platforms
- Government sources
- Telegram channels
- Other domains
"""
import re
from typing import Dict, List
from urllib.parse import urlparse


class ReferenceDetector:
    """Detect non-media references in Telegram messages."""

    # Social media domain mapping
    SOCIAL_MEDIA_DOMAINS = {
        'twitter.com': 'Twitter/X',
        'x.com': 'Twitter/X',
        'facebook.com': 'Facebook',
        'instagram.com': 'Instagram',
        'youtube.com': 'YouTube',
        'tiktok.com': 'TikTok'
    }

    # Official domain mapping
    OFFICIAL_DOMAINS = {
        'gov.ua': 'Government',
        'president.gov.ua': 'Government',
        'kmu.gov.ua': 'Government',
        'mil.gov.ua': 'Government',
        'mvs.gov.ua': 'Government',
        'mfa.gov.ua': 'Government',
        'dpsu.gov.ua': 'Government',
        'ssu.gov.ua': 'Government'
    }

    def extract_urls(self, text: str) -> List[str]:
        """
        Extract all URLs from text.

        Args:
            text: Text to extract URLs from

        Returns:
            List of URLs found
        """
        if not text:
            return []

        # URL pattern
        url_pattern = r'https?://[^\s<>"\']+'
        return re.findall(url_pattern, text)

    def extract_telegram_channels(self, text: str) -> List[str]:
        """
        Extract Telegram channel names from @mentions and t.me/ links.

        Args:
            text: Text to extract channel names from

        Returns:
            List of unique channel names
        """
        if not text:
            return []

        channels = set()

        # Extract @mentions
        mentions = re.findall(r'@(\w+)', text)
        channels.update(mentions)

        # Extract from t.me/ links
        tme_links = re.findall(r't\.me/(\w+)', text, re.IGNORECASE)
        channels.update(tme_links)

        return list(channels)

    def categorize_url(self, url: str) -> str:
        """
        Categorize a URL by its domain.

        Args:
            url: URL to categorize

        Returns:
            Category name (e.g., "Twitter/X", "Government", "Other (domain)")
        """
        try:
            parsed = urlparse(url.lower())
            domain = parsed.netloc

            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]

            # Check social media domains
            for sm_domain, category in self.SOCIAL_MEDIA_DOMAINS.items():
                if sm_domain in domain:
                    return category

            # Check official domains
            for off_domain, category in self.OFFICIAL_DOMAINS.items():
                if off_domain in domain:
                    return category

            # Return as "Other (domain)"
            return f"Other ({domain})"

        except Exception:
            return "Other (unknown)"

    def detect_references(self, message: Dict, has_media_reference: bool = False) -> Dict:
        """
        Detect non-media references in a message.

        Args:
            message: Message dictionary
            has_media_reference: Whether the message already has a media reference

        Returns:
            Dictionary with reference detection results
        """
        text = message.get('text', '') or ''

        # Extract URLs and categorize them
        urls = self.extract_urls(text)
        reference_categories = {}
        urls_by_category = {}

        for url in urls:
            category = self.categorize_url(url)

            # Count categories
            reference_categories[category] = reference_categories.get(category, 0) + 1

            # Store URLs by category
            if category not in urls_by_category:
                urls_by_category[category] = []
            urls_by_category[category].append(url)

        # Extract Telegram channels
        telegram_channels = self.extract_telegram_channels(text)
        if telegram_channels:
            reference_categories['Telegram Channels'] = len(telegram_channels)

        # Determine if there are non-media references
        has_non_media_reference = len(reference_categories) > 0

        return {
            'has_non_media_reference': has_non_media_reference,
            'reference_categories': reference_categories,
            'telegram_channels': telegram_channels,
            'urls_by_category': urls_by_category
        }

    def analyze_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Analyze non-media references for a batch of messages.

        Args:
            messages: List of message dictionaries

        Returns:
            List of messages with reference_detection field added
        """
        analyzed_messages = []

        for message in messages:
            # Create a copy of the message
            analyzed_message = message.copy()

            # Check if message has media reference
            link_detection = message.get('link_detection', {})
            mention_detection = message.get('mention_detection', {})
            similarity_detection = message.get('similarity_detection', {})

            has_media_reference = (
                link_detection.get('has_media_link', False) or
                mention_detection.get('has_media_mention', False) or
                similarity_detection.get('has_similarity_match', False)
            )

            # Add reference detection
            analyzed_message['reference_detection'] = self.detect_references(
                message, has_media_reference
            )

            analyzed_messages.append(analyzed_message)

        return analyzed_messages

    def get_statistics(self, analyzed_messages: List[Dict]) -> Dict:
        """
        Calculate reference statistics.

        Args:
            analyzed_messages: List of analyzed messages

        Returns:
            Dictionary with statistics
        """
        total_messages = len(analyzed_messages)
        messages_with_non_media_references = 0
        reference_category_counts = {}
        all_telegram_channels = set()
        messages_without_media = 0
        without_media_but_with_other_refs = 0

        for message in analyzed_messages:
            # Get detection results
            link_detection = message.get('link_detection', {})
            mention_detection = message.get('mention_detection', {})
            similarity_detection = message.get('similarity_detection', {})
            reference_detection = message.get('reference_detection', {})

            has_media_reference = (
                link_detection.get('has_media_link', False) or
                mention_detection.get('has_media_mention', False) or
                similarity_detection.get('has_similarity_match', False)
            )

            if not has_media_reference:
                messages_without_media += 1

            # Count messages with non-media references
            if reference_detection.get('has_non_media_reference', False):
                messages_with_non_media_references += 1

                # Count messages without media but with other refs
                if not has_media_reference:
                    without_media_but_with_other_refs += 1

            # Aggregate reference categories
            for category, count in reference_detection.get('reference_categories', {}).items():
                reference_category_counts[category] = reference_category_counts.get(category, 0) + count

            # Collect unique Telegram channels
            channels = reference_detection.get('telegram_channels', [])
            all_telegram_channels.update(channels)

        # Calculate percentages
        percentage_with_non_media_references = (
            (messages_with_non_media_references / total_messages * 100)
            if total_messages > 0 else 0
        )

        without_media_percentage_with_refs = (
            (without_media_but_with_other_refs / messages_without_media * 100)
            if messages_without_media > 0 else 0
        )

        return {
            'total_messages': total_messages,
            'messages_with_non_media_references': messages_with_non_media_references,
            'percentage_with_non_media_references': percentage_with_non_media_references,
            'reference_category_counts': reference_category_counts,
            'unique_telegram_channels_mentioned': len(all_telegram_channels),
            'telegram_channels_list': sorted(list(all_telegram_channels)),
            'messages_without_media': messages_without_media,
            'without_media_but_with_other_refs': without_media_but_with_other_refs,
            'without_media_percentage_with_refs': without_media_percentage_with_refs
        }
