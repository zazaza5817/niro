import logging 
from fastapi import APIRouter, status, Response # type: ignore
from models.subscription import SubscriptionCheckResponse
import services.users as user_service
logger = logging.getLogger("my_app")

router = APIRouter()


@router.get("/check_subscription", response_model=SubscriptionCheckResponse, status_code=status.HTTP_200_OK)
async def check_subscription(auth_data: str):
    return await user_service.check_subscription(auth_data)


@router.get("/sub/{jwt_token}")
async def get_subscription(jwt_token: str):
    print(f"Request to /sub/{jwt_token} router")
    logger.info(f"Request to /sub/{jwt_token}")
    try:
        html_content, headers = await user_service.get_subscription(jwt_token)
        logger.info(f"Generated HTML content for jwt_token: {jwt_token}")
        logger.debug(f"Headers: {headers}")
        
        response = Response(content=html_content, media_type="text/html")
        
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value
            
        return response
    except Exception as e:
        logger.error(f"error on /sub/{jwt_token} {e}")
        print(f"error on /sub/{jwt_token} {e} router")
        raise e
