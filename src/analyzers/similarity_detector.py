"""Semantic similarity detector for finding rephrased content."""
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from src.utils.config import SIMILARITY_THRESHOLD, TIME_WINDOW_HOURS


class SimilarityDetector:
    """Detects semantically similar content between media and Telegram."""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Initialize the similarity detector.

        Args:
            model_name: Name of the sentence transformer model
        """
        print(f"Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.threshold = SIMILARITY_THRESHOLD
        self.time_window_hours = TIME_WINDOW_HOURS

    def encode_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Encode texts into embeddings.

        Args:
            texts: List of texts to encode
            batch_size: Batch size for encoding

        Returns:
            Array of embeddings
        """
        return self.model.encode(texts, batch_size=batch_size, show_progress_bar=True)

    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score (0-1)
        """
        return np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )

    def is_within_time_window(
        self, telegram_date: str, media_date: Optional[str]
    ) -> bool:
        """
        Check if Telegram message is within time window after media article.

        Args:
            telegram_date: Telegram message date (ISO format)
            media_date: Media article date (ISO format)

        Returns:
            True if within time window
        """
        if not media_date:
            return True  # If we don't know media date, don't filter by time

        try:
            # Parse dates and ensure they're timezone-aware
            tg_dt = datetime.fromisoformat(telegram_date.replace("Z", "+00:00"))
            media_dt = datetime.fromisoformat(media_date.replace("Z", "+00:00"))

            # Make timezone-aware if naive
            if tg_dt.tzinfo is None:
                tg_dt = tg_dt.replace(tzinfo=timezone.utc)
            if media_dt.tzinfo is None:
                media_dt = media_dt.replace(tzinfo=timezone.utc)

            # Telegram message should be after media article
            if tg_dt < media_dt:
                return False

            # Check time window
            time_diff = tg_dt - media_dt
            return time_diff <= timedelta(hours=self.time_window_hours)

        except Exception as e:
            print(f"Error parsing dates: {e}")
            return True

    def find_similar_articles(
        self,
        telegram_message: Dict,
        media_articles: List[Dict],
        media_embeddings: np.ndarray,
    ) -> List[Dict]:
        """
        Find media articles similar to a Telegram message.

        Args:
            telegram_message: Telegram message dictionary
            media_articles: List of media article dictionaries
            media_embeddings: Pre-computed embeddings for media articles

        Returns:
            List of similar articles with similarity scores
        """
        # Encode Telegram message
        tg_text = telegram_message.get("text", "")
        if not tg_text or len(tg_text) < 50:  # Skip very short messages
            return []

        tg_embedding = self.model.encode([tg_text])[0]

        similar_articles = []

        for i, (article, media_emb) in enumerate(zip(media_articles, media_embeddings)):
            # Check time window first
            if not self.is_within_time_window(
                telegram_message["date"], article.get("publish_date")
            ):
                continue

            # Compute similarity
            similarity = self.compute_similarity(tg_embedding, media_emb)

            if similarity >= self.threshold:
                similar_articles.append(
                    {
                        "article": article,
                        "similarity_score": float(similarity),
                    }
                )

        # Sort by similarity score
        similar_articles.sort(key=lambda x: x["similarity_score"], reverse=True)

        return similar_articles

    def analyze_messages(
        self, telegram_messages: List[Dict], media_articles: List[Dict]
    ) -> List[Dict]:
        """
        Analyze Telegram messages for semantic similarity with media articles.

        Args:
            telegram_messages: List of Telegram messages
            media_articles: List of media articles

        Returns:
            List of messages with similarity detection results
        """
        if not media_articles:
            print("No media articles to compare against")
            return telegram_messages

        # Pre-compute embeddings for media articles
        print("Encoding media articles...")
        media_texts = [
            f"{article.get('title', '')} {article.get('text', '')}"
            for article in media_articles
        ]
        media_embeddings = self.encode_texts(media_texts)

        # Analyze each Telegram message
        print("Analyzing Telegram messages...")
        results = []

        for message in tqdm(telegram_messages, desc="Finding similar articles"):
            similar = self.find_similar_articles(message, media_articles, media_embeddings)

            detection = {
                "has_similar_content": len(similar) > 0,
                "similar_articles": similar[:5],  # Keep top 5
                "detection_method": "semantic_similarity",
            }

            result = {**message, "similarity_detection": detection}
            results.append(result)

        return results

    def get_statistics(self, analyzed_messages: List[Dict]) -> Dict:
        """
        Get statistics about similarity detection.

        Args:
            analyzed_messages: Messages with similarity detection results

        Returns:
            Statistics dictionary
        """
        total = len(analyzed_messages)
        with_similar = sum(
            1 for msg in analyzed_messages
            if msg.get("similarity_detection", {}).get("has_similar_content", False)
        )

        # Get distribution of similarity scores
        all_scores = []
        for msg in analyzed_messages:
            similar = msg.get("similarity_detection", {}).get("similar_articles", [])
            for article in similar:
                all_scores.append(article["similarity_score"])

        return {
            "total_messages": total,
            "messages_with_similar_content": with_similar,
            "percentage_with_similar_content": (with_similar / total * 100) if total > 0 else 0,
            "avg_similarity_score": np.mean(all_scores) if all_scores else 0,
            "max_similarity_score": max(all_scores) if all_scores else 0,
            "min_similarity_score": min(all_scores) if all_scores else 0,
        }
