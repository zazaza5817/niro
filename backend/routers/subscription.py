import logging 
from fastapi import APIRouter, Response # type: ignore
from services.users import UserService

logger = logging.getLogger("my_app")

router = APIRouter()


@router.get("/sub/{jwt_token}")
async def get_subscription(jwt_token: str):
    """Получает конфигурацию VPN по JWT токену."""
    logger.info(f"Request to /sub/{jwt_token}")
    try:
        html_content, headers = await UserService.get_subscription(jwt_token)
        logger.info(f"Generated HTML content for jwt_token: {jwt_token}")
        
        response = Response(content=html_content, media_type="text/html")
        
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value
            
        return response
    except Exception as e:
        logger.error(f"error on /sub/{jwt_token} {e}")
        raise e
