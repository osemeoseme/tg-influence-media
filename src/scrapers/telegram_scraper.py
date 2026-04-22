"""Telegram channel scraper using Telethon API."""
import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict
from telethon import TelegramClient
from telethon.tl.types import Message
from telethon.errors import SessionPasswordNeededError
from tqdm import tqdm

from src.utils.config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_PHONE,
    MAX_MESSAGES_PER_CHANNEL,
    RAW_DATA_DIR,
    load_telegram_channels,
    get_start_date,
)

# Session file location
SESSION_FILE = "telegram_session"


class TelegramScraper:
    """Scraper for Telegram channels."""

    def __init__(self, force_rescrape: bool = False, skip_existing: bool = True):
        """
        Initialize the Telegram scraper.

        Args:
            force_rescrape: If True, rescrape all channels even if data exists
            skip_existing: If True, skip channels that already have data files
        """
        self.client = None
        self.channels = load_telegram_channels()
        self.force_rescrape = force_rescrape
        self.skip_existing = skip_existing

    async def init_client(self):
        """Initialize Telegram client with interactive authentication."""
        print("\n🔐 Initializing Telegram connection...")

        if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
            raise ValueError(
                "❌ TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file"
            )

        print(f"   API ID: {TELEGRAM_API_ID}")
        print(f"   Phone: {TELEGRAM_PHONE or 'Not set - will prompt'}")

        self.client = TelegramClient(SESSION_FILE, TELEGRAM_API_ID, TELEGRAM_API_HASH)

        print("\n📱 Connecting to Telegram...")
        await self.client.connect()

        if not await self.client.is_user_authorized():
            print("\n⚠️  Not authorized - authentication required")
            print("=" * 60)

            # Get phone number
            phone = TELEGRAM_PHONE
            if not phone:
                phone = input("📞 Enter your phone number (with country code, e.g., +1234567890): ")
            else:
                print(f"📞 Using phone number from .env: {phone}")

            # Send code request
            print(f"\n📤 Sending authentication code to {phone}...")
            await self.client.send_code_request(phone)

            # Get code from user
            print("📨 A code has been sent to your Telegram app")
            code = input("🔢 Enter the code you received: ")

            try:
                # Sign in with code
                print("\n🔑 Signing in...")
                await self.client.sign_in(phone, code)
                print("✅ Successfully authenticated!")

            except SessionPasswordNeededError:
                # 2FA is enabled
                print("\n🔒 Two-factor authentication is enabled")
                password = input("🔐 Enter your 2FA password: ")
                await self.client.sign_in(password=password)
                print("✅ Successfully authenticated with 2FA!")

            print(f"💾 Session saved to: {SESSION_FILE}.session")
            print("   (You won't need to authenticate again)")
        else:
            print("✅ Already authenticated (using saved session)")

        # Verify connection
        me = await self.client.get_me()
        print(f"👤 Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or 'N/A'})")
        print("=" * 60)

    async def scrape_channel(self, channel_username: str, channel_name: str) -> List[Dict]:
        """
        Scrape messages from a Telegram channel.

        Args:
            channel_username: Channel username (without @)
            channel_name: Human-readable channel name

        Returns:
            List of message dictionaries
        """
        # Check if data already exists
        output_file = RAW_DATA_DIR / f"telegram_{channel_username}.json"
        if output_file.exists() and self.skip_existing and not self.force_rescrape:
            print(f"⏭️  Skipping {channel_name} (@{channel_username}) - data already exists at {output_file}")
            print(f"   Use force_rescrape=True to re-download")
            # Load and return existing data
            with open(output_file, "r", encoding="utf-8") as f:
                existing_messages = json.load(f)
            print(f"   Loaded {len(existing_messages)} existing messages")
            return existing_messages

        print(f"\n📥 Scraping channel: {channel_name} (@{channel_username})")

        # Get start date from configuration (supports START_DATE from .env)
        date_limit = get_start_date()
        print(f"   📅 Collecting messages from {date_limit.date()} onwards")
        print(f"   📊 Limit: {MAX_MESSAGES_PER_CHANNEL:,} messages")

        messages = []
        message_count = 0
        skipped_old = 0

        try:
            print(f"   🔍 Looking up channel entity...")
            entity = await self.client.get_entity(channel_username)
            print(f"   ✅ Found channel: {entity.title}")

            print(f"   ⬇️  Downloading messages...")

            # Create progress bar
            pbar = tqdm(
                total=MAX_MESSAGES_PER_CHANNEL,
                desc=f"   Messages",
                unit="msg",
                file=sys.stdout
            )

            async for message in self.client.iter_messages(
                entity, limit=MAX_MESSAGES_PER_CHANNEL
            ):
                message_count += 1
                pbar.update(1)

                # Stop if message is older than date limit
                if message.date < date_limit:
                    skipped_old += 1
                    pbar.set_postfix({"collected": len(messages), "too_old": skipped_old})
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

                # Update progress with stats
                pbar.set_postfix({"collected": len(messages), "checked": message_count})

            pbar.close()

        except Exception as e:
            print(f"\n❌ Error scraping {channel_username}: {type(e).__name__}: {e}")
            import traceback
            print("   Traceback:")
            traceback.print_exc()

            # If partial data was collected, save it anyway
            if messages:
                print(f"⚠️  Saving {len(messages)} partial messages before error")
                temp_file = RAW_DATA_DIR / f"telegram_{channel_username}_partial.json"
                try:
                    with open(temp_file, "w", encoding="utf-8") as f:
                        json.dump(messages, f, ensure_ascii=False, indent=2)
                    print(f"   💾 Partial data saved to {temp_file}")
                except Exception as save_error:
                    print(f"   ❌ Could not save partial data: {save_error}")
            return messages

        print(f"\n✅ Collected {len(messages):,} messages from {channel_name}")
        if skipped_old > 0:
            print(f"   ⏭️  Stopped early - reached messages older than {date_limit.date()}")
        return messages

    async def scrape_all_channels(self) -> Dict[str, List[Dict]]:
        """
        Scrape all configured Telegram channels.

        Returns:
            Dictionary mapping channel usernames to their messages
        """
        print(f"\n📋 Total channels to process: {len(self.channels)}")
        print("=" * 60)

        await self.init_client()

        all_messages = {}
        successful = 0
        skipped = 0
        failed = 0

        for idx, channel in enumerate(self.channels, 1):
            username = channel["username"]
            name = channel["name"]

            print(f"\n[{idx}/{len(self.channels)}] Processing: {name}")
            print("-" * 60)

            messages = await self.scrape_channel(username, name)
            all_messages[username] = messages

            # Save individual channel data (only if new data was scraped)
            output_file = RAW_DATA_DIR / f"telegram_{username}.json"
            if messages and (not output_file.exists() or self.force_rescrape):
                try:
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(messages, f, ensure_ascii=False, indent=2)
                    file_size = output_file.stat().st_size / 1024 / 1024  # MB
                    print(f"💾 Saved to {output_file} ({file_size:.2f} MB)")
                    successful += 1
                except Exception as e:
                    print(f"❌ Error saving file: {e}")
                    failed += 1
            else:
                skipped += 1

            # Small delay between channels to be respectful to Telegram API
            if idx < len(self.channels):
                print(f"⏸️  Waiting 2 seconds before next channel...")
                await asyncio.sleep(2)

        print("\n" + "=" * 60)
        print("📊 SCRAPING SUMMARY")
        print("=" * 60)
        print(f"✅ Successful: {successful}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"❌ Failed: {failed}")
        print(f"📝 Total: {len(self.channels)}")
        print("=" * 60)

        print("\n🔌 Disconnecting from Telegram...")
        await self.client.disconnect()
        print("✅ Disconnected")

        return all_messages

    def save_all_messages(self, all_messages: Dict[str, List[Dict]]):
        """
        Save all messages to a single file.
        Merges with existing data if present to avoid data loss.
        """
        output_file = RAW_DATA_DIR / "telegram_all_messages.json"

        # Load existing data if present
        existing_data = {}
        if output_file.exists():
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                print(f"📂 Found existing data file with {len(existing_data)} channels")
            except Exception as e:
                print(f"⚠️  Could not load existing data: {e}")

        # Merge new data with existing (new data takes precedence)
        merged_data = {**existing_data, **all_messages}

        # Create backup before overwriting
        if output_file.exists():
            backup_file = RAW_DATA_DIR / f"telegram_all_messages_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import shutil
            shutil.copy2(output_file, backup_file)
            print(f"🔄 Created backup at {backup_file}")

        # Save merged data
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)

        total_messages = sum(len(msgs) for msgs in merged_data.values())
        print(f"💾 Saved all messages to {output_file}")
        print(f"   Total: {len(merged_data)} channels, {total_messages} messages")


async def main():
    """Main function to run the scraper."""
    scraper = TelegramScraper()
    all_messages = await scraper.scrape_all_channels()
    scraper.save_all_messages(all_messages)


if __name__ == "__main__":
    asyncio.run(main())
