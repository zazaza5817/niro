from backend.services.internal_auth import verify_internal_api_key
from fastapi import APIRouter, status, Query, Depends # type: ignore
from typing import List, Optional
from config import settings
from services.payments import PaymentService
from services.pricing import PricingService
from models.pricing import PlanPriceRequest, PlanWithDiscount, PriceInfo
from models.payment import SelectPlanRequest

router = APIRouter()


@router.post("/select_plan", status_code=status.HTTP_200_OK)
async def select_plan(request: SelectPlanRequest):
   """Отправляет пользователю инвойс для оплаты выбранного плана"""
   await PaymentService.select_plan(request.selected_plan, request.auth_data)
   return {"response": "OK"}

@router.get("/get_plans", response_model=List[PlanWithDiscount], status_code=status.HTTP_200_OK)
async def get_plans(user_tg_id: Optional[int] = Query(None)):
    """Получает список планов с учетом реферальных планов пользователя"""
    return await PricingService.get_plans_with_discount(user_tg_id)
