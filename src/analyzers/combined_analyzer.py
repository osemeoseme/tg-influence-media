"""Combined analyzer that uses all detection methods."""
import json
from typing import List, Dict
from pathlib import Path

from src.analyzers.link_detector import LinkDetector
from src.analyzers.mention_detector import MentionDetector
from src.analyzers.similarity_detector import SimilarityDetector
from src.utils.config import PROCESSED_DATA_DIR, RESULTS_DIR


class CombinedAnalyzer:
    """Combines all detection methods to analyze media influence."""

    def __init__(self):
        """Initialize the combined analyzer."""
        self.link_detector = LinkDetector()
        self.mention_detector = MentionDetector()
        self.similarity_detector = SimilarityDetector()

    def analyze_channel(
        self, telegram_messages: List[Dict], media_articles: List[Dict], channel_name: str
    ) -> Dict:
        """
        Analyze a Telegram channel for media influence.

        Args:
            telegram_messages: List of Telegram messages
            media_articles: List of media articles
            channel_name: Name of the channel

        Returns:
            Analysis results dictionary
        """
        print(f"\n{'='*60}")
        print(f"Analyzing channel: {channel_name}")
        print(f"{'='*60}")

        # Step 1: Detect direct links
        print("\n1. Detecting direct links to media...")
        messages_with_links = self.link_detector.analyze_messages(telegram_messages)
        link_stats = self.link_detector.get_statistics(messages_with_links)
        print(f"   Found {link_stats['messages_with_media_links']} messages with media links "
              f"({link_stats['percentage_with_media_links']:.2f}%)")

        # Step 2: Detect media mentions
        print("\n2. Detecting media mentions...")
        messages_with_mentions = self.mention_detector.analyze_messages(messages_with_links)
        mention_stats = self.mention_detector.get_statistics(messages_with_mentions)
        print(f"   Found {mention_stats['messages_with_media_mentions']} messages with mentions "
              f"({mention_stats['percentage_with_media_mentions']:.2f}%)")

        # Step 3: Detect semantic similarity (only for messages without links/mentions)
        print("\n3. Detecting semantic similarity...")
        # Filter messages that don't have links or mentions
        messages_for_similarity = [
            msg for msg in messages_with_mentions
            if not msg.get("link_detection", {}).get("has_media_link", False)
            and not msg.get("mention_detection", {}).get("has_media_mention", False)
        ]

        print(f"   Checking {len(messages_for_similarity)} messages for similarity...")
        messages_with_similarity = self.similarity_detector.analyze_messages(
            messages_for_similarity, media_articles
        )
        similarity_stats = self.similarity_detector.get_statistics(messages_with_similarity)
        print(f"   Found {similarity_stats['messages_with_similar_content']} messages with similar content")

        # Combine all results
        all_analyzed = self._combine_results(
            messages_with_mentions, messages_with_similarity
        )

        # Calculate overall statistics
        overall_stats = self._calculate_overall_stats(
            all_analyzed, link_stats, mention_stats, similarity_stats
        )

        return {
            "channel_name": channel_name,
            "messages": all_analyzed,
            "statistics": overall_stats,
        }

    def _combine_results(
        self, messages_with_mentions: List[Dict], messages_with_similarity: List[Dict]
    ) -> List[Dict]:
        """Combine results from all detection methods."""
        # Create a dictionary for quick lookup
        similarity_dict = {msg["id"]: msg for msg in messages_with_similarity}

        combined = []
        for msg in messages_with_mentions:
            # If message was analyzed for similarity, add those results
            if msg["id"] in similarity_dict:
                sim_msg = similarity_dict[msg["id"]]
                msg["similarity_detection"] = sim_msg.get("similarity_detection", {})

            combined.append(msg)

        return combined

    def _calculate_overall_stats(
        self,
        all_messages: List[Dict],
        link_stats: Dict,
        mention_stats: Dict,
        similarity_stats: Dict,
    ) -> Dict:
        """Calculate overall statistics across all detection methods."""
        total = len(all_messages)

        # Count messages influenced by media (any detection method)
        influenced_count = 0
        link_only = 0
        mention_only = 0
        similarity_only = 0
        multiple_methods = 0

        for msg in all_messages:
            has_link = msg.get("link_detection", {}).get("has_media_link", False)
            has_mention = msg.get("mention_detection", {}).get("has_media_mention", False)
            has_similarity = msg.get("similarity_detection", {}).get("has_similar_content", False)

            detection_count = sum([has_link, has_mention, has_similarity])

            if detection_count > 0:
                influenced_count += 1

                if detection_count == 1:
                    if has_link:
                        link_only += 1
                    elif has_mention:
                        mention_only += 1
                    elif has_similarity:
                        similarity_only += 1
                else:
                    multiple_methods += 1

        return {
            "total_messages": total,
            "influenced_by_media": influenced_count,
            "percentage_influenced": (influenced_count / total * 100) if total > 0 else 0,
            "detection_breakdown": {
                "link_only": link_only,
                "mention_only": mention_only,
                "similarity_only": similarity_only,
                "multiple_methods": multiple_methods,
            },
            "by_method": {
                "links": link_stats,
                "mentions": mention_stats,
                "similarity": similarity_stats,
            },
        }

    def save_results(self, results: Dict, output_file: Path):
        """Save analysis results to file."""
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to: {output_file}")
