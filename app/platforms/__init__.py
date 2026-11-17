"""Platform integrations package exporting all supported platforms."""
from app.platforms.base import BasePlatform
from app.platforms.telegram import TelegramPlatform
from app.platforms.discord import DiscordPlatform
from app.platforms.slack import SlackPlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.github import GitHubPlatform
from app.platforms.devto import DevToPlatform

__all__ = [
    "BasePlatform",
    "TelegramPlatform",
    "DiscordPlatform",
    "SlackPlatform",
    "MastodonPlatform",
    "GitHubPlatform",
    "DevToPlatform",
]
