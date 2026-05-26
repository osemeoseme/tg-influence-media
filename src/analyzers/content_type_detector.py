"""Content Type Detector for Telegram messages.

Detects different types of content in messages:
- Government sources (gov.ua domains)
- Official channels (government/military keywords)
- Social media links
- Telegram channel mentions
- News (default)
"""
import re
from typing import Dict, List


class ContentTypeDetector:
    """Detect content types in Telegram messages."""

    # Government domains
    GOV_DOMAINS = [
        'gov.ua',
        'president.gov.ua',
        'kmu.gov.ua',
        'mil.gov.ua',
        'mvs.gov.ua',
        'mfa.gov.ua',
        'dpsu.gov.ua',
        'ssu.gov.ua'
    ]

    # Official channel keyword patterns
    OFFICIAL_KEYWORDS = [
        r'голова.*ОВА',
        r'ОВА\b',
        r'ДСНС',
        r'ЗСУ',
        r'Генштаб',
        r'Міноборони',
        r'МВС',
        r'СБУ',
        r'ДПСУ',
        r'офіційн',
        r'прес-служб'
    ]

    # Social media domains
    SOCIAL_MEDIA_DOMAINS = [
        'twitter.com',
        'x.com',
        'facebook.com',
        'instagram.com',
        'youtube.com'
    ]

    def __init__(self):
        """Initialize the content type detector."""
        # Compile official channel patterns
        self.official_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.OFFICIAL_KEYWORDS
        ]

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

    def is_gov_url(self, url: str) -> bool:
        """
        Check if URL is from a government source.

        Args:
            url: URL to check

        Returns:
            True if URL is from government domain
        """
        url_lower = url.lower()
        return any(domain in url_lower for domain in self.GOV_DOMAINS)

    def detect_telegram_channel_mention(self, text: str) -> bool:
        """
        Detect if text mentions a Telegram channel.

        Args:
            text: Text to check

        Returns:
            True if Telegram channel mention found
        """
        if not text:
            return False

        # Check for @mentions
        if re.search(r'@\w+', text):
            return True

        # Check for t.me/ links
        if 't.me/' in text.lower():
            return True

        return False

    def detect_content_type(self, message: Dict) -> Dict:
        """
        Detect content type(s) in a message.

        Args:
            message: Message dictionary

        Returns:
            Dictionary with content type detection results
        """
        text = message.get('text', '') or ''
        content_types = []
        primary_source = None

        # Extract URLs
        urls = self.extract_urls(text)

        # Check for government sources
        gov_urls = [url for url in urls if self.is_gov_url(url)]
        has_gov_source = len(gov_urls) > 0
        if has_gov_source:
            content_types.append('government_source')
            primary_source = 'government_source'

        # Check for official channel keywords
        has_official_channel = any(
            pattern.search(text)
            for pattern in self.official_patterns
        )
        if has_official_channel and not primary_source:
            content_types.append('official_channel')
            primary_source = 'official_channel'

        # Check for social media links
        social_urls = [
            url for url in urls
            if any(domain in url.lower() for domain in self.SOCIAL_MEDIA_DOMAINS)
        ]
        has_social_media = len(social_urls) > 0
        if has_social_media:
            content_types.append('social_media')

        # Check for Telegram channel mentions
        has_tg_channel_mention = self.detect_telegram_channel_mention(text)
        if has_tg_channel_mention:
            content_types.append('telegram_channel')

        # Add news as primary source if no other primary source detected
        if not primary_source:
            content_types.append('news')

        return {
            'content_types': content_types,
            'has_gov_source': has_gov_source,
            'gov_urls': gov_urls,
            'has_official_channel': has_official_channel,
            'has_social_media': has_social_media,
            'social_urls': social_urls,
            'has_tg_channel_mention': has_tg_channel_mention
        }

    def analyze_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Analyze content types for a batch of messages.

        Args:
            messages: List of message dictionaries

        Returns:
            List of messages with content_type_detection field added
        """
        analyzed_messages = []

        for message in messages:
            # Create a copy of the message
            analyzed_message = message.copy()

            # Add content type detection
            analyzed_message['content_type_detection'] = self.detect_content_type(message)

            analyzed_messages.append(analyzed_message)

        return analyzed_messages

    def get_statistics(self, analyzed_messages: List[Dict]) -> Dict:
        """
        Calculate content type statistics.

        Args:
            analyzed_messages: List of analyzed messages

        Returns:
            Dictionary with statistics
        """
        total_messages = len(analyzed_messages)
        content_type_counts = {}

        # Count each content type
        for message in analyzed_messages:
            detection = message.get('content_type_detection', {})
            for content_type in detection.get('content_types', []):
                content_type_counts[content_type] = content_type_counts.get(content_type, 0) + 1

        # Calculate percentages
        content_type_percentages = {}
        for content_type, count in content_type_counts.items():
            percentage = (count / total_messages * 100) if total_messages > 0 else 0
            content_type_percentages[content_type] = percentage

        return {
            'total_messages': total_messages,
            'content_type_counts': content_type_counts,
            'content_type_percentages': content_type_percentages
        }
