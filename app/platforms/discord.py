from typing import Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
import httpx
from app.platforms.base import BasePlatform


class DiscordPlatform(BasePlatform):
    """
    Integration with Discord Webhook API.
    Official Documentation: https://discord.com/developers/docs/resources/webhook#execute-webhook
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        mock_mode: bool = False,
    ):
        super().__init__(mock_mode=mock_mode)
        self.webhook_url = webhook_url

    @property
    def name(self) -> str:
        return "Discord"

    def is_configured(self) -> bool:
        return bool(self.webhook_url and self.webhook_url.startswith("http"))

    def missing_credentials_message(self) -> str:
        return "Missing Discord credentials: DISCORD_WEBHOOK_URL must be set in .env"

    def _get_mock_result(self, cta_url: str) -> Tuple[str, bool]:
        return "https://discord.com/channels/123456789012345678/987654321098765432/112233445566778899", True

    async def _publish(
        self, message: str, cta_url: str, client: httpx.AsyncClient
    ) -> Tuple[str, bool]:
        # Ensure 'wait=true' query parameter is present so Discord returns the created message object
        parsed_url = urlparse(self.webhook_url)
        query = parse_qs(parsed_url.query)
        query["wait"] = ["true"]
        new_query = urlencode(query, doseq=True)
        target_url = urlunparse(parsed_url._replace(query=new_query))

        payload = {
            "content": message,
        }

        response = await client.post(target_url, json=payload, timeout=10.0)
        response.raise_for_status()

        data = response.json()
        message_id = data.get("id")
        channel_id = data.get("channel_id")
        guild_id = data.get("guild_id", "@me")

        if message_id and channel_id:
            posted_url = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
        else:
            posted_url = self.webhook_url

        # Public access is True for public Discord community/announcement channels
        public_access = True
        return posted_url, public_access
