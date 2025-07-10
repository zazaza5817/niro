from pydantic import BaseModel # type: ignore
from typing import Optional, List
from datetime import datetime


class ReferralCode(BaseModel):
    id: Optional[int] = None
    code: str
    max_uses: Optional[int] = None
    current_uses: int = 0
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True


class CreateReferralRequest(BaseModel):
    max_uses: Optional[int] = None
    expires_days: Optional[int] = None


class ReferralResponse(BaseModel):
    id: int
    code: str
    referral_link: str
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None


class ApplyReferralRequest(BaseModel):
    user_tg_id: int
    referral_code: str


class ReferralPlan(BaseModel):
    id: Optional[int] = None
    referral_code_id: int
    is_default: bool = False
    default_plan_payload: Optional[str] = None  # payload из plans.json
    discount_percent: int = 0
    # Кастомные поля плана
    price: Optional[int] = None
    duration: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    label: Optional[str] = None
    payload: Optional[str] = None
    name: Optional[str] = None
    price_per_month: Optional[int] = None
    created_at: Optional[datetime] = None


class AddReferralPlanRequest(BaseModel):
    referral_code_id: int
    is_default: bool
    discount_percent: int = 0
    # Если is_default = True, используется только этот payload
    default_plan_payload: Optional[str] = None
    # Если is_default = False, используются все эти поля
    price: Optional[int] = None
    duration: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    label: Optional[str] = None
    payload: Optional[str] = None
    name: Optional[str] = None
    price_per_month: Optional[int] = None


class ReferralPlanResponse(BaseModel):
    id: int
    referral_code_id: int
    is_default: bool
    discount_percent: int
    # Поля плана (заполняются либо из дефолтного, либо кастомные)
    price: int
    duration: int
    title: str
    description: str
    label: str
    payload: str
    name: str
    price_per_month: int
    created_at: Optional[datetime] = None


class ReferralCodeWithPlans(BaseModel):
    id: int
    code: str
    max_uses: Optional[int] = None
    current_uses: int = 0
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    plans: List[ReferralPlanResponse] = []