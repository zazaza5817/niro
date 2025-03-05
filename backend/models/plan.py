from pydantic import BaseModel

class Plan(BaseModel):
   name: str
   price_per_month: int