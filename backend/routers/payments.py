from fastapi import APIRouter, status # type: ignore
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
    plans_list = []
    for key, plan in settings.plans.items():
        plans_list.append({
            "id": key, 
            "name": plan["name"],
            "price_per_month": plan["price_per_month"]
        })
    return plans_list
