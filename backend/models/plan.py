from pydantic import BaseModel # type: ignore
from typing import Optional


class Plan(BaseModel):
   id: str
   name: str
   price_per_month: int
   original_price: Optional[int] = None
   discount_percent: Optional[int] = None