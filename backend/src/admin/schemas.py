from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class AdminLoginRequest(BaseModel):
    username: EmailStr
    password: str

class UserAdminView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str] = None
    email: EmailStr
    is_active: bool
    is_superuser: bool
    is_premium: Optional[bool] = None
    created_at: Optional[datetime] = None