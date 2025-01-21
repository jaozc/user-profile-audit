from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserProfileBase(BaseModel):
    name: str
    email: EmailStr

class UserProfileCreate(UserProfileBase):
    pass

class UserProfile(UserProfileBase):
    id: str = Field(..., description="ID único do usuário")
    is_deleted: bool = Field(..., description="Indica se o usuário foi deletado")
    
    class Config:
        from_attributes = True 