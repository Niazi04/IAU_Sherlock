from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.core.security import verify_api_key

from app.core.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(
    api_key: Optional[str] = Security(_api_key_header),
) -> str:
    if api_key is None or not verify_api_key(api_key, settings.UI_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Internal API key.",
        )
    return api_key