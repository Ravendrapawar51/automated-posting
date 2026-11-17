from typing import Optional, Tuple
import httpx
from app.platforms.base import BasePlatform


class GitHubPlatform(BasePlatform):
    """
    Integration with GitHub REST API (Issues / Announcements Portal).
    Official Documentation: https://docs.github.com/en/rest/issues/issues#create-an-issue
    """

    def __init__(
        self,
        access_token: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
        mock_mode: bool = False,
    ):
        super().__init__(mock_mode=mock_mode)
        self.access_token = access_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name

    @property
    def name(self) -> str:
        return "GitHub"

    def is_configured(self) -> bool:
        return bool(self.access_token and self.repo_owner and self.repo_name)

    def missing_credentials_message(self) -> str:
        return "Missing GitHub credentials: GITHUB_ACCESS_TOKEN, GITHUB_REPO_OWNER, and GITHUB_REPO_NAME must be set in .env"

    def _get_mock_result(self, cta_url: str) -> Tuple[str, bool]:
        owner = self.repo_owner or "octocat"
        repo = self.repo_name or "announcements"
        return f"https://github.com/{owner}/{repo}/issues/42", True

    async def _publish(
        self, message: str, cta_url: str, client: httpx.AsyncClient
    ) -> Tuple[str, bool]:
        api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Short summary title from the message
        snippet = message.split(".")[0][:50]
        title = f"Announcement: {snippet}" if snippet else "Platform Announcement"

        payload = {
            "title": title,
            "body": message,
            "labels": ["announcement", "automated-posting"],
        }

        response = await client.post(
            api_url, headers=headers, json=payload, timeout=10.0
        )
        response.raise_for_status()

        data = response.json()
        posted_url = data.get("html_url")
        if not posted_url:
            issue_number = data.get("number")
            posted_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/issues/{issue_number}"

        # GitHub issues in public repositories are publicly accessible
        public_access = True
        return posted_url, public_access
