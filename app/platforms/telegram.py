from typing import Optional, Tuple
import httpx
from app.platforms.base import BasePlatform


class TelegramPlatform(BasePlatform):
    """
    Integration with Telegram Bot API.
    Official Documentation: https://core.telegram.org/bots/api#sendmessage
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        mock_mode: bool = False,
    ):
        super().__init__(mock_mode=mock_mode)
        self.bot_token = bot_token
        self.chat_id = chat_id

    @property
    def name(self) -> str:
        return "Telegram"

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def missing_credentials_message(self) -> str:
        return "Missing Telegram credentials: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env"

    def _get_mock_result(self, cta_url: str) -> Tuple[str, bool]:
        channel = (self.chat_id or "@example_channel").lstrip("@")
        return f"https://t.me/{channel}/1042", True

    async def _publish(
        self, message: str, cta_url: str, client: httpx.AsyncClient
    ) -> Tuple[str, bool]:
        api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "disable_web_page_preview": False,
        }

        response = await client.post(api_url, json=payload, timeout=10.0)
        response.raise_for_status()

        data = response.json()
        if not data.get("ok"):
            raise ValueError(
                f"Telegram API returned ok=False: {data.get('description', 'Unknown error')}"
            )

        result = data.get("result", {})
        message_id = result.get("message_id")
        chat = result.get("chat", {})
        chat_username = chat.get("username")

        # Determine public permalink
        if chat_username:
            posted_url = f"https://t.me/{chat_username}/{message_id}"
            public_access = True
        elif self.chat_id and self.chat_id.startswith("@"):
            posted_url = f"https://t.me/{self.chat_id.lstrip('@')}/{message_id}"
            public_access = True
        else:
            raw_id = str(chat.get("id", self.chat_id or ""))
            # Telegram channel IDs with -100 prefix in web links
            if raw_id.startswith("-100"):
                link_id = raw_id[4:]
                posted_url = f"https://t.me/c/{link_id}/{message_id}"
            else:
                posted_url = f"https://t.me/c/{raw_id}/{message_id}"
            public_access = False

        return posted_url, public_access
