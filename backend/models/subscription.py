from typing import Optional
from pydantic import BaseModel

class SubscriptionCheckResponse(BaseModel):
    status: str
    display_text: str
    config_url: Optional[str] = None