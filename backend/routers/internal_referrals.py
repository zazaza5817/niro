import logging
from fastapi import APIRouter, status, Depends # type: ignore
from typing import List
from models.referral import (
    CreateReferralRequest, ReferralResponse, ApplyReferralRequest, 
    AddReferralPlanRequest, ReferralPlanResponse
)
from services.referrals import ReferralService
from services.internal_auth import verify_internal_api_key

logger = logging.getLogger("my_app")
router = APIRouter()


@router.post("/apply_referral", dependencies=[Depends(verify_internal_api_key)])
async def apply_referral_code_internal(request: ApplyReferralRequest):
    """Применяет реферальный код для пользователя"""
    logger.info(f"Internal request: applying referral code {request.referral_code} for user {request.user_tg_id}")
    success = await ReferralService.apply_referral_code(request.user_tg_id, request.referral_code)
    if success:
        return {"success": True, "message": "Реферальный код успешно применен"}
    else:
        return {"success": False, "message": "Код недействителен или уже использован"}

@router.post("/create_referral", response_model=ReferralResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_internal_api_key)])
async def create_referral_code_internal(request: CreateReferralRequest):
    """Создает новый реферальный код"""
    logger.info(f"Internal request: creating referral code")
    return await ReferralService.create_referral_code(request)

@router.post("/add_ref_plan", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_internal_api_key)])
async def add_referral_plan_internal(request: AddReferralPlanRequest):
    """Добавляет план к реферальному коду"""
    logger.info(f"Internal request: adding plan to referral code {request.referral_code_id}")
    plan_id = await ReferralService.add_referral_plan(request)
    if plan_id:
        return {"message": "Plan added successfully", "plan_id": plan_id}
    else:
        return {"error": "Failed to add plan"}


@router.post("/deactivate_referral/{referral_code}", dependencies=[Depends(verify_internal_api_key)])
async def deactivate_referral_code_internal(referral_code: str):
    """Деактивирует реферальный код"""
    logger.info(f"Internal request: deactivating referral code {referral_code}")
    success = await ReferralService.deactivate_referral_code(referral_code)
    if success:
        return {"message": f"Referral code {referral_code} deactivated successfully"}
    else:
        return {"error": f"Failed to deactivate referral code {referral_code}"}

@router.delete("/referral_plan/{plan_id}", dependencies=[Depends(verify_internal_api_key)])
async def delete_referral_plan_internal(plan_id: int):
    """Удаляет план реферального кода"""
    logger.info(f"Internal request: deleting referral plan {plan_id}")
    success = await ReferralService.delete_referral_plan(plan_id)
    if success:
        return {"message": f"Referral plan {plan_id} deleted successfully"}
    else:
        return {"error": f"Failed to delete referral plan {plan_id}"}


@router.get("/referral_plans_by_code/{referral_code}", response_model=List[ReferralPlanResponse], dependencies=[Depends(verify_internal_api_key)])
async def get_referral_plans_by_code_internal(referral_code: str):
    """Получает планы по реферальному коду"""
    logger.info(f"Internal request: getting plans for referral code {referral_code}")
    return await ReferralService.get_referral_plans_by_code(referral_code)

# есть ручка но и внутри бека используется
@router.get("/user_referral_plans/{user_tg_id}", response_model=List[ReferralPlanResponse], dependencies=[Depends(verify_internal_api_key)])
async def get_user_referral_plans_internal(user_tg_id: int):
    """Получает все реферальные планы пользователя"""
    logger.info(f"Internal request: getting referral plans for user {user_tg_id}")
    return await ReferralService.get_user_referral_plans(user_tg_id)
