from pydantic import BaseModel # type: ignore

class Plan(BaseModel):
   id: str
   name: str
   price_per_month: int