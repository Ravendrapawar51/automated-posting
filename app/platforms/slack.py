from typing import Optional, Tuple
import httpx
from app.platforms.base import BasePlatform


class SlackPlatform(BasePlatform):
    """
    Integration with Slack Incoming Webhooks and Slack Web API.
    Official Documentation:
      - Webhooks: https://api.slack.com/messaging/webhooks
      - chat.postMessage: https://api.slack.com/methods/chat.postMessage
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        bot_token: Optional[str] = None,
        channel_id: Optional[str] = None,
        mock_mode: bool = False,
    ):
        super().__init__(mock_mode=mock_mode)
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.channel_id = channel_id

    @property
    def name(self) -> str:
        return "Slack"

    def is_configured(self) -> bool:
        has_webhook = bool(self.webhook_url and self.webhook_url.startswith("http"))
        has_bot = bool(self.bot_token and self.channel_id)
        return has_webhook or has_bot

    def missing_credentials_message(self) -> str:
        return "Missing Slack credentials: Provide SLACK_WEBHOOK_URL or both SLACK_BOT_TOKEN and SLACK_CHANNEL_ID in .env"

    def _get_mock_result(self, cta_url: str) -> Tuple[str, bool]:
        channel = self.channel_id or "C0123456789"
        return f"https://app.slack.com/client/T01234567/{channel}/p1698765432100000", False

    async def _publish(
        self, message: str, cta_url: str, client: httpx.AsyncClient
    ) -> Tuple[str, bool]:
        # Path A: Slack Web API (chat.postMessage)
        if self.bot_token and self.channel_id:
            api_url = "https://slack.com/api/chat.postMessage"
            headers = {
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "channel": self.channel_id,
                "text": message,
            }
            response = await client.post(
                api_url, headers=headers, json=payload, timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                raise ValueError(
                    f"Slack API error: {data.get('error', 'unknown_error')}"
                )

            channel = data.get("channel", self.channel_id)
            ts = data.get("ts", "")
            clean_ts = ts.replace(".", "")
            posted_url = f"https://app.slack.com/client/archive/{channel}/p{clean_ts}"
            return posted_url, False

        # Path B: Slack Incoming Webhook
        elif self.webhook_url:
            payload = {"text": message}
            response = await client.post(
                self.webhook_url, json=payload, timeout=10.0
            )
            response.raise_for_status()

            # Slack webhooks respond with text "ok"
            if response.text.strip().lower() != "ok":
                raise ValueError(
                    f"Unexpected Slack webhook response: {response.text[:200]}"
                )

            # Slack webhooks do not return message permalinks; link to Slack workspace
            posted_url = "https://app.slack.com/client/"
            return posted_url, False

        else:
            raise ValueError(self.missing_credentials_message())
