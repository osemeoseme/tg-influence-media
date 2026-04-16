"""Telegram channel scraper using Telethon API."""
import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict
from telethon import TelegramClient
from telethon.tl.types import Message
from tqdm import tqdm

from src.utils.config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_PHONE,
    DATA_MONTHS_BACK,
    MAX_MESSAGES_PER_CHANNEL,
    RAW_DATA_DIR,
    load_telegram_channels,
)


class TelegramScraper:
    """Scraper for Telegram channels."""

    def __init__(self):
        """Initialize the Telegram scraper."""
        self.client = None
        self.channels = load_telegram_channels()

    async def init_client(self):
        """Initialize Telegram client."""
        if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
            raise ValueError(
                "TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file"
            )

        self.client = TelegramClient("session", TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await self.client.start(phone=TELEGRAM_PHONE)

    async def scrape_channel(self, channel_username: str, channel_name: str) -> List[Dict]:
        """
        Scrape messages from a Telegram channel.

        Args:
            channel_username: Channel username (without @)
            channel_name: Human-readable channel name

        Returns:
            List of message dictionaries
        """
        print(f"Scraping channel: {channel_name} (@{channel_username})")

        # Calculate date limit (timezone-aware to match Telegram message dates)
        date_limit = datetime.now(timezone.utc) - timedelta(days=30 * DATA_MONTHS_BACK)

        messages = []
        try:
            entity = await self.client.get_entity(channel_username)

            async for message in self.client.iter_messages(
                entity, limit=MAX_MESSAGES_PER_CHANNEL
            ):
                # Stop if message is older than date limit
                if message.date < date_limit:
                    break

                # Extract message data
                message_data = {
                    "id": message.id,
                    "date": message.date.isoformat(),
                    "text": message.text or "",
                    "views": message.views,
                    "forwards": message.forwards,
                    "channel_username": channel_username,
                    "channel_name": channel_name,
                }

                # Extract URLs from entities
                urls = []
                if message.entities:
                    for entity in message.entities:
                        if hasattr(entity, "url") and entity.url:
                            urls.append(entity.url)

                # Also extract URLs from text
                if message.text:
                    import re
                    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
                    urls.extend(re.findall(url_pattern, message.text))

                message_data["urls"] = list(set(urls))  # Remove duplicates

                messages.append(message_data)

        except Exception as e:
            print(f"Error scraping {channel_username}: {e}")

        print(f"Collected {len(messages)} messages from {channel_name}")
        return messages

    async def scrape_all_channels(self) -> Dict[str, List[Dict]]:
        """
        Scrape all configured Telegram channels.

        Returns:
            Dictionary mapping channel usernames to their messages
        """
        await self.init_client()

        all_messages = {}

        for channel in tqdm(self.channels, desc="Scraping channels"):
            username = channel["username"]
            name = channel["name"]

            messages = await self.scrape_channel(username, name)
            all_messages[username] = messages

            # Save individual channel data
            output_file = RAW_DATA_DIR / f"telegram_{username}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)

        await self.client.disconnect()
        return all_messages

    def save_all_messages(self, all_messages: Dict[str, List[Dict]]):
        """Save all messages to a single file."""
        output_file = RAW_DATA_DIR / "telegram_all_messages.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_messages, f, ensure_ascii=False, indent=2)
        print(f"Saved all messages to {output_file}")


async def main():
    """Main function to run the scraper."""
    scraper = TelegramScraper()
    all_messages = await scraper.scrape_all_channels()
    scraper.save_all_messages(all_messages)


if __name__ == "__main__":
    asyncio.run(main())
