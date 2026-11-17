import logging
from contextlib import asynccontextmanager
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.schemas import PostingRequest, PostingResponse
from app.services.posting_service import PostingService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("automated_posting")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Starting Automated Multi-Platform Posting Service...")
    logger.info(f"Mock Mode: {settings.MOCK_MODE}")
    yield
    logger.info("Shutting down Automated Multi-Platform Posting Service...")


app = FastAPI(
    title="Automated Multi-Platform Posting System API",
    description=(
        "Production-grade FastAPI service that automatically broadcasts messages and CTA links "
        "across multiple third-party platforms (Telegram, Discord, Slack, Mastodon, GitHub, Dev.to) "
        "with complete fault isolation and input validation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize posting service
posting_service = PostingService(config=settings)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Standardized, human-readable error handler for request validation failures.
    Returns HTTP 422 with precise validation error messages.
    """
    error_messages = []
    for err in exc.errors():
        loc = " -> ".join(str(p) for p in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        # Strip internal Pydantic prefix if present
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]
        error_messages.append(f"{loc}: {msg}")

    logger.warning(f"Request validation failed: {error_messages}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation Error",
            "message": error_messages[0] if len(error_messages) == 1 else "Input validation failed",
            "details": error_messages,
        },
    )


@app.get(
    "/",
    tags=["System"],
    summary="Root Information",
    description="Returns service status and available platform integrations.",
)
async def root() -> Dict[str, Any]:
    return {
        "service": "Automated Multi-Platform Posting System",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoint": "POST /posting",
        "supported_platforms": [p.name for p in posting_service.platforms],
        "mock_mode": settings.MOCK_MODE,
    }


@app.get(
    "/health",
    tags=["System"],
    summary="Health Check",
    description="Returns the operational health of the service.",
)
async def health_check() -> Dict[str, str]:
    return {"status": "healthy"}


@app.post(
    "/posting",
    response_model=PostingResponse,
    status_code=status.HTTP_200_OK,
    tags=["Posting"],
    summary="Publish short message across multiple platforms",
    description=(
        "Accepts a short message (max 200 chars) containing exactly one valid CTA link, "
        "validates input, and broadcasts it across all configured third-party platforms. "
        "Failures on any single platform do not prevent other platforms from publishing."
    ),
    responses={
        200: {
            "description": "Posting results for all platforms",
            "model": PostingResponse,
        },
        422: {
            "description": "Validation error (message > 200 chars, missing CTA, multiple CTAs, or invalid URL)",
        },
    },
)
async def publish_post(payload: PostingRequest) -> PostingResponse:
    """
    Core posting endpoint. Validates input and triggers parallel broadcasting.
    """
    logger.info(f"Received posting request with message: '{payload.message}'")
    cta_url = payload.cta_url

    response = await posting_service.broadcast(
        message=payload.message,
        cta_url=cta_url,
    )

    logger.info(
        f"Broadcast finished. Overall success: {response.success}, "
        f"Platforms: {len(response.results)}"
    )
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
