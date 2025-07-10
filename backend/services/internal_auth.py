import logging
from fastapi import HTTPException, status, Header # type: ignore
from typing import Optional
import os

logger = logging.getLogger("my_app")

INTERNAL_API_KEY = os.environ.get('INTERNAL_API_KEY', 'default_internal_key_change_me_')

def verify_internal_api_key(x_internal_api_key: Optional[str] = Header(None)):
    """Проверяет внутренний API ключ для защищенных эндпоинтов"""
    if not x_internal_api_key:
        logger.warning("Missing internal API key in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Internal API key required"
        )
    
    if x_internal_api_key != INTERNAL_API_KEY:
        logger.warning(f"Invalid internal API key: {x_internal_api_key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key"
        )
    
    logger.debug("Internal API key verified successfully")
    return True
