from typing import Optional
from pydantic import BaseModel # type: ignore


class SubscriptionCheckResponse(BaseModel):
    status: str
    display_text: str
    config_url: Optional[str] = None

class SubscriptionCheckRequest(BaseModel):
    auth_data: str
