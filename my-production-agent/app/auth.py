from fastapi import Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

from app.config import settings


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    allowed = {k.strip() for k in settings.agent_api_keys.split(",") if k.strip()}
    if api_key not in allowed:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return api_key

