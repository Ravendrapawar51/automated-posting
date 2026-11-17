from typing import Optional, Tuple
import httpx
from app.platforms.base import BasePlatform


class MastodonPlatform(BasePlatform):
    """
    Integration with Mastodon REST API (Decentralized Social Media / Fediverse).
    Official Documentation: https://docs.joinmastodon.org/methods/statuses/#create
    """

    def __init__(
        self,
        instance_url: Optional[str] = "https://mastodon.social",
        access_token: Optional[str] = None,
        mock_mode: bool = False,
    ):
        super().__init__(mock_mode=mock_mode)
        self.instance_url = (instance_url or "https://mastodon.social").rstrip("/")
        self.access_token = access_token

    @property
    def name(self) -> str:
        return "Mastodon"

    def is_configured(self) -> bool:
        return bool(self.access_token and self.instance_url)

    def missing_credentials_message(self) -> str:
        return "Missing Mastodon credentials: MASTODON_ACCESS_TOKEN and MASTODON_INSTANCE_URL must be set in .env"

    def _get_mock_result(self, cta_url: str) -> Tuple[str, bool]:
        return f"{self.instance_url}/@bot/112233445566778899", True

    async def _publish(
        self, message: str, cta_url: str, client: httpx.AsyncClient
    ) -> Tuple[str, bool]:
        api_url = f"{self.instance_url}/api/v1/statuses"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "status": message,
            "visibility": "public",
        }

        response = await client.post(
            api_url, headers=headers, json=payload, timeout=10.0
        )
        response.raise_for_status()

        data = response.json()
        posted_url = data.get("url") or data.get("uri")

        if not posted_url:
            status_id = data.get("id")
            posted_url = f"{self.instance_url}/web/statuses/{status_id}"

        # Mastodon public statuses are publicly accessible
        public_access = True
        return posted_url, public_access
