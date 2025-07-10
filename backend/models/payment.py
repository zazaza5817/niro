from pydantic import BaseModel # type: ignore


class SelectPlanRequest(BaseModel):
    selected_plan: str
    auth_data: str
