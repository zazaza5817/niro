from fastapi import APIRouter, status
from typing import List
from config import settings
import services.payments as payment_service
from models.plan import Plan

router = APIRouter()


@router.post("/select_plan", status_code=status.HTTP_200_OK)
async def select_plan(selected_plan: str, auth_data: str):
   await payment_service.select_plan(selected_plan, auth_data)
   return {"response": "OK"}

@router.get("/get_plans", response_model=List[Plan], status_code=status.HTTP_200_OK)
async def get_plans():
    return list(settings.plans.values())
