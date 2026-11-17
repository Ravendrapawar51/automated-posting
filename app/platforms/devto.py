from typing import Optional, Tuple
import httpx
from app.platforms.base import BasePlatform


class DevToPlatform(BasePlatform):
    """
    Integration with Dev.to Forem API (Developer Community & Blogging Portal).
    Official Documentation: https://developers.forem.com/api/v0#tag/articles/operation/createArticle
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        organization_id: Optional[int] = None,
        mock_mode: bool = False,
    ):
        super().__init__(mock_mode=mock_mode)
        self.api_key = api_key
        self.organization_id = organization_id

    @property
    def name(self) -> str:
        return "Dev.to"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def missing_credentials_message(self) -> str:
        return "Missing Dev.to credentials: DEVTO_API_KEY must be set in .env"

    def _get_mock_result(self, cta_url: str) -> Tuple[str, bool]:
        return "https://dev.to/devuser/announcement-check-out-our-latest-platform-4821", True

    async def _publish(
        self, message: str, cta_url: str, client: httpx.AsyncClient
    ) -> Tuple[str, bool]:
        api_url = "https://dev.to/api/articles"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

        snippet = message.split(".")[0][:50]
        title = f"Announcement: {snippet}" if snippet else "Platform Announcement"

        payload = {
            "article": {
                "title": title,
                "published": True,
                "body_markdown": f"{message}\n\n*Published via Automated Multi-Platform Posting*",
                "tags": ["announcements", "news"],
            }
        }
        if self.organization_id:
            payload["article"]["organization_id"] = self.organization_id

        response = await client.post(
            api_url, headers=headers, json=payload, timeout=10.0
        )
        response.raise_for_status()

        data = response.json()
        posted_url = data.get("url") or data.get("canonical_url")
        public_access = True

        return posted_url, public_access
