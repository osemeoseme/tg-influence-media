"""Configuration utilities for the project."""
import json
import os
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"

# Create directories if they don't exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, RESULTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def load_telegram_channels() -> List[Dict]:
    """Load Telegram channels configuration."""
    with open(CONFIG_DIR / "telegram_channels.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_media_sources() -> List[Dict]:
    """Load media sources configuration."""
    with open(CONFIG_DIR / "media_sources.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_media_domains() -> List[str]:
    """Get all media domains for link detection."""
    media_sources = load_media_sources()
    domains = []
    for source in media_sources:
        domains.extend(source.get("domains", []))
    return domains


def get_media_names() -> List[str]:
    """Get all media names for mention detection."""
    media_sources = load_media_sources()
    return [source["name"] for source in media_sources]


# Telegram API settings
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE")

# Data collection settings
DATA_MONTHS_BACK = int(os.getenv("DATA_MONTHS_BACK", "3"))
MAX_MESSAGES_PER_CHANNEL = int(os.getenv("MAX_MESSAGES_PER_CHANNEL", "10000"))

# Analysis settings
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.75"))
TIME_WINDOW_HOURS = int(os.getenv("TIME_WINDOW_HOURS", "48"))
