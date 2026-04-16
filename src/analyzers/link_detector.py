"""Detector for direct links to media sources in Telegram messages."""
import re
from typing import List, Dict, Set
from urllib.parse import urlparse

from src.utils.config import get_media_domains


class LinkDetector:
    """Detects direct links to traditional media in Telegram messages."""

    def __init__(self):
        """Initialize the link detector."""
        self.media_domains = get_media_domains()

    def extract_urls(self, text: str) -> List[str]:
        """
        Extract all URLs from text.

        Args:
            text: Text to extract URLs from

        Returns:
            List of URLs
        """
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)

    def is_media_url(self, url: str) -> bool:
        """
        Check if URL is from a media source.

        Args:
            url: URL to check

        Returns:
            True if URL is from a media source
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]

            # Check if domain matches any media domain
            for media_domain in self.media_domains:
                if domain == media_domain or domain.endswith("." + media_domain):
                    return True

            return False
        except Exception:
            return False

    def detect_media_links(self, message: Dict) -> Dict:
        """
        Detect media links in a Telegram message.

        Args:
            message: Message dictionary with 'text' and 'urls' fields

        Returns:
            Dictionary with detection results
        """
        # Get URLs from message
        urls = message.get("urls", [])

        # Also extract from text
        if message.get("text"):
            text_urls = self.extract_urls(message["text"])
            urls.extend(text_urls)

        # Remove duplicates
        urls = list(set(urls))

        # Check which URLs are media links
        media_urls = [url for url in urls if self.is_media_url(url)]

        return {
            "has_media_link": len(media_urls) > 0,
            "media_urls": media_urls,
            "all_urls": urls,
            "detection_method": "direct_link",
        }

    def analyze_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Analyze multiple messages for media links.

        Args:
            messages: List of message dictionaries

        Returns:
            List of messages with link detection results
        """
        results = []
        for message in messages:
            detection = self.detect_media_links(message)
            result = {**message, "link_detection": detection}
            results.append(result)

        return results

    def get_statistics(self, analyzed_messages: List[Dict]) -> Dict:
        """
        Get statistics about media link detection.

        Args:
            analyzed_messages: Messages with link detection results

        Returns:
            Statistics dictionary
        """
        total = len(analyzed_messages)
        with_media_links = sum(
            1 for msg in analyzed_messages
            if msg.get("link_detection", {}).get("has_media_link", False)
        )

        return {
            "total_messages": total,
            "messages_with_media_links": with_media_links,
            "percentage_with_media_links": (with_media_links / total * 100) if total > 0 else 0,
        }
