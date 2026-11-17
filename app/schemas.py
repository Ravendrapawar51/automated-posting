import re
from typing import List, Optional
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator, model_validator


def extract_and_validate_cta_url(message: str) -> str:
    """
    Extracts and validates that the message contains exactly one valid CTA link.
    Raises ValueError with descriptive messages upon violation.
    """
    if not message or not message.strip():
        raise ValueError("Message cannot be empty or whitespace only.")

    if len(message) > 200:
        raise ValueError(
            f"Message must not exceed 200 characters (received {len(message)} characters)."
        )

    # Detect all URL patterns (schemes like http://, https://, ftp://, or www. prefixes)
    raw_urls = re.findall(
        r"(?:[a-zA-Z][a-zA-Z0-9+.-]*://|www\.)[^\s<>'\"`]+",
        message,
        re.IGNORECASE,
    )

    # Strip trailing punctuation frequently typed at the end of sentences
    cleaned_urls = []
    for raw in raw_urls:
        cleaned = re.sub(r"[.,!?:;)'\"]+$", "", raw)
        if cleaned:
            cleaned_urls.append(cleaned)

    if len(cleaned_urls) == 0:
        raise ValueError("Message must contain exactly one CTA link, but none was found.")

    if len(cleaned_urls) > 1:
        raise ValueError(
            f"Message must contain exactly one CTA link, but {len(cleaned_urls)} were found: {', '.join(cleaned_urls)}."
        )

    target_url = cleaned_urls[0]

    # Handle protocol requirement
    if target_url.lower().startswith("www."):
        raise ValueError(
            f"CTA link '{target_url}' is missing an HTTP/HTTPS protocol scheme (e.g., https://{target_url})."
        )

    parsed = urlparse(target_url)

    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError(
            f"CTA link '{target_url}' uses unsupported scheme '{parsed.scheme}'. Only http:// and https:// are permitted."
        )

    hostname = parsed.hostname
    if not hostname:
        raise ValueError(f"CTA link '{target_url}' is missing a valid hostname.")

    # Domain structure validation
    if hostname.startswith(".") or hostname.endswith(".") or ".." in hostname:
        raise ValueError(f"CTA link '{target_url}' contains an invalid domain structure.")

    # Localhost is valid for dev/testing, otherwise require at least one dot for a TLD
    if hostname != "localhost" and "." not in hostname:
        raise ValueError(
            f"CTA link '{target_url}' does not have a valid top-level domain (TLD)."
        )

    return target_url


class PostingRequest(BaseModel):
    """Incoming request payload for multi-platform posting."""

    message: str = Field(
        ...,
        description="The message to be broadcasted across platforms. Must be <= 200 characters and contain exactly one valid CTA link.",
        examples=[
            "Check out our latest business platform and grow your online visibility. https://example.com"
        ],
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        # Runs length and CTA URL extraction & validation
        extract_and_validate_cta_url(v)
        return v

    @property
    def cta_url(self) -> str:
        """Returns the extracted and validated single CTA URL."""
        return extract_and_validate_cta_url(self.message)


class PlatformResult(BaseModel):
    """Result of posting to a single platform."""

    platform: str = Field(..., description="Platform name")
    status: str = Field(..., description="Success or Failed")
    posted_url: Optional[str] = Field(
        None, description="Published content URL or permalink"
    )
    public_access: bool = Field(
        False, description="Whether the posted content is publicly accessible"
    )
    date: Optional[str] = Field(
        None, description="Posting date in YYYY-MM-DD format"
    )
    time: Optional[str] = Field(
        None, description="Posting time in HH:MM:SS format"
    )
    error: Optional[str] = Field(
        None, description="Error details or exception message if failed"
    )


class PostingResponse(BaseModel):
    """Aggregated response containing results across all integrated platforms."""

    success: bool = Field(
        ...,
        description="True if posting succeeded on at least one platform, False if all failed",
    )
    results: List[PlatformResult] = Field(
        ..., description="List of individual platform posting results"
    )
