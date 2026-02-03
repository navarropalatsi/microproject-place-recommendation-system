from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette import status

from app.config.settings import settings

api_key_header_scheme = APIKeyHeader(name=settings.SERVICE_AK_HEADER, auto_error=False)


def validate_security_token(api_key_header: str = Security(api_key_header_scheme)):
    if not api_key_header or api_key_header != settings.SERVICE_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return api_key_header
