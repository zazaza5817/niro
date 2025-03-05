from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    tg_id: int
    status: str
    expiry: Optional[str] = None
    jwt_token: Optional[str] = None
    connection_link: Optional[str] = None
    server_id: Optional[int] = None