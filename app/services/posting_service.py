import asyncio
import logging
from typing import List, Optional
import httpx

from app.config import Settings, settings as default_settings
from app.platforms.base import BasePlatform
from app.platforms.telegram import TelegramPlatform
from app.platforms.discord import DiscordPlatform
from app.platforms.slack import SlackPlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.github import GitHubPlatform
from app.platforms.devto import DevToPlatform
from app.schemas import PlatformResult, PostingResponse

logger = logging.getLogger(__name__)


class PostingService:
    """
    Coordinates and executes automated message broadcasting across all supported platforms.
    Guarantees fault-isolation so a failure on one platform never halts the others.
    """

    def __init__(
        self,
        config: Optional[Settings] = None,
        platforms: Optional[List[BasePlatform]] = None,
    ):
        self.config = config or default_settings
        self.platforms: List[BasePlatform] = platforms or self._initialize_platforms()

    def _initialize_platforms(self) -> List[BasePlatform]:
        """Instantiates all supported platforms using loaded environment credentials."""
        mock = self.config.MOCK_MODE

        return [
            TelegramPlatform(
                bot_token=self.config.TELEGRAM_BOT_TOKEN,
                chat_id=self.config.TELEGRAM_CHAT_ID,
                mock_mode=mock,
            ),
            DiscordPlatform(
                webhook_url=self.config.DISCORD_WEBHOOK_URL,
                mock_mode=mock,
            ),
            SlackPlatform(
                webhook_url=self.config.SLACK_WEBHOOK_URL,
                bot_token=self.config.SLACK_BOT_TOKEN,
                channel_id=self.config.SLACK_CHANNEL_ID,
                mock_mode=mock,
            ),
            MastodonPlatform(
                instance_url=self.config.MASTODON_INSTANCE_URL,
                access_token=self.config.MASTODON_ACCESS_TOKEN,
                mock_mode=mock,
            ),
            GitHubPlatform(
                access_token=self.config.GITHUB_ACCESS_TOKEN,
                repo_owner=self.config.GITHUB_REPO_OWNER,
                repo_name=self.config.GITHUB_REPO_NAME,
                mock_mode=mock,
            ),
            DevToPlatform(
                api_key=self.config.DEVTO_API_KEY,
                organization_id=self.config.DEVTO_ORGANIZATION_ID,
                mock_mode=mock,
            ),
        ]

    async def broadcast(self, message: str, cta_url: str) -> PostingResponse:
        """
        Publishes the message and CTA URL across all registered platforms concurrently.
        Each platform is handled independently with full fault isolation.
        """
        results: List[PlatformResult] = []

        logger.info(
            f"Starting broadcast to {len(self.platforms)} platforms. Message length: {len(message)}, CTA: {cta_url}"
        )

        # Use an async HTTP client with sensible connection pooling and timeouts
        async with httpx.AsyncClient(timeout=15.0) as client:
            tasks = [
                platform.post(message=message, cta_url=cta_url, client=client)
                for platform in self.platforms
            ]

            # asyncio.gather with return_exceptions=True guarantees an uncaught error in one task
            # cannot cause gather to fail or abort other tasks
            gathered_results = await asyncio.gather(*tasks, return_exceptions=True)

            for platform, outcome in zip(self.platforms, gathered_results):
                if isinstance(outcome, PlatformResult):
                    results.append(outcome)
                elif isinstance(outcome, Exception):
                    logger.error(
                        f"Unhandled exception returned from platform {platform.name}: {outcome}",
                        exc_info=outcome,
                    )
                    results.append(
                        PlatformResult(
                            platform=platform.name,
                            status="failed",
                            posted_url=None,
                            public_access=False,
                            date=None,
                            time=None,
                            error=f"Internal error: {str(outcome)}",
                        )
                    )
                else:
                    results.append(
                        PlatformResult(
                            platform=platform.name,
                            status="failed",
                            posted_url=None,
                            public_access=False,
                            date=None,
                            time=None,
                            error="Unknown execution outcome",
                        )
                    )

        # Overall success is True if at least one platform successfully published
        overall_success = any(r.status == "success" for r in results)

        return PostingResponse(
            success=overall_success,
            results=results,
        )
