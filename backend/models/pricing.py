from pydantic import BaseModel # type: ignore
from typing import List, Optional


class GetPlansRequest(BaseModel):
    user_tg_id: Optional[int] = None


class PlanPriceRequest(BaseModel):
    user_tg_id: int
    plan_payload: str


class PlanWithDiscount(BaseModel):
    id: str
    name: str
    price_per_month: int
    original_price: Optional[int] = None
    discount_percent: Optional[int] = None


class PriceInfo(BaseModel):
   price: int
