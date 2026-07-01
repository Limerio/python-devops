"""API key authentication dependency."""

import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

API_KEY = os.getenv("API_KEY") or "dev-key-change-me"


async def verify_api_key(key: str = Security(api_key_header)) -> str:
    """Reject requests without a valid API key."""
    if not key or key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
    return key
