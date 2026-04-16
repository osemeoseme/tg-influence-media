"""Detector for media mentions in Telegram messages."""
import re
from typing import List, Dict, Set

from src.utils.config import get_media_names, load_media_sources


class MentionDetector:
    """Detects mentions of traditional media in Telegram messages."""

    def __init__(self):
        """Initialize the mention detector."""
        self.media_names = get_media_names()
        self.media_sources = load_media_sources()

        # Create patterns for each media source
        self.media_patterns = self._create_patterns()

    def _create_patterns(self) -> Dict[str, List[str]]:
        """
        Create regex patterns for each media source.

        Returns:
            Dictionary mapping media names to their patterns
        """
        patterns = {}

        for source in self.media_sources:
            name = source["name"]
            source_patterns = []

            # Add exact name pattern
            source_patterns.append(re.escape(name))

            # Add domain-based patterns
            for domain in source.get("domains", []):
                # Remove TLD for matching
                domain_name = domain.split(".")[0]
                if domain_name not in name.lower():
                    source_patterns.append(re.escape(domain_name))

            patterns[name] = source_patterns

        return patterns

    def detect_mentions(self, message: Dict) -> Dict:
        """
        Detect media mentions in a Telegram message.

        Args:
            message: Message dictionary with 'text' field

        Returns:
            Dictionary with detection results
        """
        text = message.get("text", "")
        if not text:
            return {
                "has_media_mention": False,
                "mentioned_media": [],
                "detection_method": "mention",
            }

        mentioned_media = []

        # Check for each media source
        for media_name, patterns in self.media_patterns.items():
            for pattern in patterns:
                # Case-insensitive search
                if re.search(pattern, text, re.IGNORECASE):
                    mentioned_media.append(media_name)
                    break  # Don't count the same media multiple times

        return {
            "has_media_mention": len(mentioned_media) > 0,
            "mentioned_media": mentioned_media,
            "detection_method": "mention",
        }

    def analyze_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Analyze multiple messages for media mentions.

        Args:
            messages: List of message dictionaries

        Returns:
            List of messages with mention detection results
        """
        results = []
        for message in messages:
            detection = self.detect_mentions(message)
            result = {**message, "mention_detection": detection}
            results.append(result)

        return results

    def get_statistics(self, analyzed_messages: List[Dict]) -> Dict:
        """
        Get statistics about media mention detection.

        Args:
            analyzed_messages: Messages with mention detection results

        Returns:
            Statistics dictionary
        """
        total = len(analyzed_messages)
        with_media_mentions = sum(
            1 for msg in analyzed_messages
            if msg.get("mention_detection", {}).get("has_media_mention", False)
        )

        # Count mentions per media
        media_mention_counts = {}
        for msg in analyzed_messages:
            mentioned = msg.get("mention_detection", {}).get("mentioned_media", [])
            for media in mentioned:
                media_mention_counts[media] = media_mention_counts.get(media, 0) + 1

        return {
            "total_messages": total,
            "messages_with_media_mentions": with_media_mentions,
            "percentage_with_media_mentions": (with_media_mentions / total * 100) if total > 0 else 0,
            "mention_counts_by_media": media_mention_counts,
        }
