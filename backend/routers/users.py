import logging 
from fastapi import APIRouter, status # type: ignore
from models.subscription import SubscriptionCheckResponse, SubscriptionCheckRequest
from services.users import UserService
logger = logging.getLogger("my_app")

router = APIRouter()


@router.post("/check_subscription", response_model=SubscriptionCheckResponse, status_code=status.HTTP_200_OK)
async def check_subscription(request: SubscriptionCheckRequest):
    """Возвращает информацию о подписке пользователя."""
    return await UserService.check_subscription(request.auth_data)
