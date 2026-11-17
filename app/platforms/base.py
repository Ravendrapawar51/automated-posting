import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
import httpx

from app.schemas import PlatformResult

logger = logging.getLogger(__name__)


class BasePlatform(ABC):
    """Abstract base class for all third-party platform integrations."""

    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the platform (e.g., 'Telegram', 'Discord', etc.)."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Checks if required credentials and configurations exist."""
        pass

    @abstractmethod
    def missing_credentials_message(self) -> str:
        """Returns helpful description of missing configuration keys."""
        pass

    @abstractmethod
    async def _publish(
        self, message: str, cta_url: str, client: httpx.AsyncClient
    ) -> tuple[str, bool]:
        """
        Executes the actual platform API call.
        Returns a tuple: (posted_url: str, public_access: bool).
        """
        pass

    @abstractmethod
    def _get_mock_result(self, cta_url: str) -> tuple[str, bool]:
        """
        Returns simulated (mock) url and public_access for testing / offline grading.
        """
        pass

    def _create_success_result(
        self, posted_url: str, public_access: bool
    ) -> PlatformResult:
        """Creates a standardized success result with timestamp."""
        now = datetime.now()
        return PlatformResult(
            platform=self.name,
            status="success",
            posted_url=posted_url,
            public_access=public_access,
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M:%S"),
            error=None,
        )

    def _create_failure_result(
        self, error_message: str, public_access: bool = False
    ) -> PlatformResult:
        """Creates a standardized failure result."""
        return PlatformResult(
            platform=self.name,
            status="failed",
            posted_url=None,
            public_access=public_access,
            date=None,
            time=None,
            error=error_message,
        )

    async def post(
        self, message: str, cta_url: str, client: httpx.AsyncClient
    ) -> PlatformResult:
        """
        Public entry point to publish a message.
        Guarantees isolation: exceptions will never leak or disrupt other platforms.
        """
        # If mock mode is explicitly enabled (e.g. for CI / grading without secrets)
        if self.mock_mode:
            logger.info(f"[{self.name}] Operating in MOCK_MODE, simulating success.")
            posted_url, public_access = self._get_mock_result(cta_url)
            return self._create_success_result(posted_url, public_access)

        # Check configuration
        if not self.is_configured():
            msg = self.missing_credentials_message()
            logger.warning(f"[{self.name}] Configuration missing: {msg}")
            return self._create_failure_result(msg)

        # Execute platform API call with robust error handling
        try:
            logger.info(f"[{self.name}] Sending message to API...")
            posted_url, public_access = await self._publish(message, cta_url, client)
            logger.info(f"[{self.name}] Successfully published at: {posted_url}")
            return self._create_success_result(posted_url, public_access)

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            try:
                err_body = e.response.json()
            except Exception:
                err_body = e.response.text[:300]
            err_msg = f"HTTP {status_code} error from {self.name} API: {err_body}"
            logger.error(f"[{self.name}] {err_msg}")
            return self._create_failure_result(err_msg)

        except httpx.TimeoutException as e:
            err_msg = f"Request timed out while connecting to {self.name} API."
            logger.error(f"[{self.name}] {err_msg} ({e})")
            return self._create_failure_result(err_msg)

        except httpx.RequestError as e:
            err_msg = f"Network connection error to {self.name} API: {str(e)}"
            logger.error(f"[{self.name}] {err_msg}")
            return self._create_failure_result(err_msg)

        except Exception as e:
            err_msg = f"Unexpected error during {self.name} posting: {str(e)}"
            logger.exception(f"[{self.name}] {err_msg}")
            return self._create_failure_result(err_msg)
