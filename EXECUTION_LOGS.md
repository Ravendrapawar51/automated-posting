# Automated Multi-Platform Posting System - Execution Proof & Test Logs

This document contains terminal and live API execution logs verifying the full functionality, validation checks, fault isolation, and responses of the application.

---

## 1. Automated Test Suite Execution (`pytest tests -v`)

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\raven\.gemini\antigravity\scratch\automated-posting\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\raven\.gemini\antigravity\scratch\automated-posting
configfile: pytest.ini
plugins: anyio-4.16.0, asyncio-1.5.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 17 items

tests/test_posting.py::TestInputValidation::test_valid_message_single_url PASSED [  5%]
tests/test_posting.py::TestInputValidation::test_valid_message_with_query_params PASSED [ 11%]
tests/test_posting.py::TestInputValidation::test_trailing_punctuation_stripped PASSED [ 17%]
tests/test_posting.py::TestInputValidation::test_exceeding_200_characters PASSED [ 23%]
tests/test_posting.py::TestInputValidation::test_missing_cta_link PASSED [ 29%]
tests/test_posting.py::TestInputValidation::test_multiple_cta_links PASSED [ 35%]
tests/test_posting.py::TestInputValidation::test_unsupported_scheme PASSED [ 41%]
tests/test_posting.py::TestInputValidation::test_missing_scheme_www PASSED [ 47%]
tests/test_posting.py::TestInputValidation::test_empty_message PASSED    [ 52%]
tests/test_posting.py::TestAPIEndpoints::test_root_endpoint PASSED       [ 58%]
tests/test_posting.py::TestAPIEndpoints::test_health_endpoint PASSED     [ 64%]
tests/test_posting.py::TestAPIEndpoints::test_api_validation_error_over_200_chars PASSED [ 70%]
tests/test_posting.py::TestAPIEndpoints::test_api_validation_error_no_cta_link PASSED [ 76%]
tests/test_posting.py::TestAPIEndpoints::test_api_validation_error_multiple_cta_links PASSED [ 82%]
tests/test_posting.py::TestAPIEndpoints::test_posting_in_mock_mode PASSED [ 88%]
tests/test_posting.py::TestAPIEndpoints::test_unconfigured_platforms_fail_gracefully PASSED [ 94%]
tests/test_posting.py::TestAPIEndpoints::test_fault_isolation_partial_failure PASSED [100%]

============================== 17 passed in 1.30s ===============================
```

---

## 2. API Demonstrations via Live Server (`POST http://localhost:4000/posting`)

### Scenario A: Successful Multi-Platform Broadcasting (`MOCK_MODE=true`)

**Request:**
```http
POST /posting HTTP/1.1
Host: localhost:4000
Content-Type: application/json

{
  "message": "Check out our latest business platform and grow your online visibility. https://example.com"
}
```

**Response (`200 OK`):**
```json
{
  "success": true,
  "results": [
    {
      "platform": "Telegram",
      "status": "success",
      "posted_url": "https://t.me/example_channel/1042",
      "public_access": true,
      "date": "2026-11-17",
      "time": "17:27:17",
      "error": null
    },
    {
      "platform": "Discord",
      "status": "success",
      "posted_url": "https://discord.com/channels/123456789012345678/987654321098765432/112233445566778899",
      "public_access": true,
      "date": "2026-11-17",
      "time": "17:27:17",
      "error": null
    },
    {
      "platform": "Slack",
      "status": "success",
      "posted_url": "https://app.slack.com/client/T01234567/C0123456789/p1698765432100000",
      "public_access": false,
      "date": "2026-11-17",
      "time": "17:27:17",
      "error": null
    },
    {
      "platform": "Mastodon",
      "status": "success",
      "posted_url": "https://mastodon.social/@bot/112233445566778899",
      "public_access": true,
      "date": "2026-11-17",
      "time": "17:27:17",
      "error": null
    },
    {
      "platform": "GitHub",
      "status": "success",
      "posted_url": "https://github.com/octocat/announcements/issues/42",
      "public_access": true,
      "date": "2026-11-17",
      "time": "17:27:17",
      "error": null
    },
    {
      "platform": "Dev.to",
      "status": "success",
      "posted_url": "https://dev.to/devuser/announcement-check-out-our-latest-platform-4821",
      "public_access": true,
      "date": "2026-11-17",
      "time": "17:27:17",
      "error": null
    }
  ]
}
```

---

### Scenario B: Graceful Failure Handling for Unconfigured Platforms (Fault Isolation)

When credentials are not configured in `.env`, platforms report `failed` with diagnostic details instead of crashing the server or interrupting other platforms.

**Request:**
```http
POST /posting HTTP/1.1
Host: localhost:4000
Content-Type: application/json

{
  "message": "Check out our latest business platform and grow your online visibility. https://example.com"
}
```

**Response (`200 OK`):**
```json
{
  "success": false,
  "results": [
    {
      "platform": "Telegram",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Missing Telegram credentials: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env"
    },
    {
      "platform": "Discord",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Missing Discord credentials: DISCORD_WEBHOOK_URL must be set in .env"
    },
    {
      "platform": "Slack",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Missing Slack credentials: Provide SLACK_WEBHOOK_URL or both SLACK_BOT_TOKEN and SLACK_CHANNEL_ID in .env"
    },
    {
      "platform": "Mastodon",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Missing Mastodon credentials: MASTODON_ACCESS_TOKEN and MASTODON_INSTANCE_URL must be set in .env"
    },
    {
      "platform": "GitHub",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Missing GitHub credentials: GITHUB_ACCESS_TOKEN, GITHUB_REPO_OWNER, and GITHUB_REPO_NAME must be set in .env"
    },
    {
      "platform": "Dev.to",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Missing Dev.to credentials: DEVTO_API_KEY must be set in .env"
    }
  ]
}
```

---

### Scenario C: Input Validation - Missing CTA Link

**Request:**
```http
POST /posting HTTP/1.1
Host: localhost:4000
Content-Type: application/json

{
  "message": "Announcement without any link at all."
}
```

**Response (`422 Unprocessable Entity`):**
```json
{
  "success": false,
  "error": "Validation Error",
  "message": "body -> message: Message must contain exactly one CTA link, but none was found.",
  "details": [
    "body -> message: Message must contain exactly one CTA link, but none was found."
  ]
}
```

---

### Scenario D: Input Validation - Multiple CTA Links

**Request:**
```http
POST /posting HTTP/1.1
Host: localhost:4000
Content-Type: application/json

{
  "message": "Visit https://site-one.com and check https://site-two.org!"
}
```

**Response (`422 Unprocessable Entity`):**
```json
{
  "success": false,
  "error": "Validation Error",
  "message": "body -> message: Message must contain exactly one CTA link, but 2 were found: https://site-one.com, https://site-two.org.",
  "details": [
    "body -> message: Message must contain exactly one CTA link, but 2 were found: https://site-one.com, https://site-two.org."
  ]
}
```

---

### Scenario E: Input Validation - Message Exceeding 200 Characters (206 characters)

**Request:**
```http
POST /posting HTTP/1.1
Host: localhost:4000
Content-Type: application/json

{
  "message": "Discover our innovative cloud platform delivering enterprise grade multi channel broadcasting capabilities designed to scale seamlessly across organizations of all sizes worldwide today. https://example.com"
}
```

**Response (`422 Unprocessable Entity`):**
```json
{
  "success": false,
  "error": "Validation Error",
  "message": "body -> message: Message must not exceed 200 characters (received 206 characters).",
  "details": [
    "body -> message: Message must not exceed 200 characters (received 206 characters)."
  ]
}
```

---

### Scenario F: Input Validation - Unsupported Protocol Scheme (`ftp://`)

**Request:**
```http
POST /posting HTTP/1.1
Host: localhost:4000
Content-Type: application/json

{
  "message": "Download file from ftp://mirror.example.com/installer.iso"
}
```

**Response (`422 Unprocessable Entity`):**
```json
{
  "success": false,
  "error": "Validation Error",
  "message": "body -> message: CTA link 'ftp://mirror.example.com/installer.iso' uses unsupported scheme 'ftp'. Only http:// and https:// are permitted.",
  "details": [
    "body -> message: CTA link 'ftp://mirror.example.com/installer.iso' uses unsupported scheme 'ftp'. Only http:// and https:// are permitted."
  ]
}
```
