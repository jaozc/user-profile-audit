from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Base model for user profile containing common attributes
class UserProfileBase(BaseModel):
    name: str  # Name of the user
    email: EmailStr  # Email of the user, validated as an email format

# Model for creating a new user profile, inherits from UserProfileBase
class UserProfileCreate(UserProfileBase):
    pass  # No additional fields for creation

# Model representing a user profile with additional attributes
class UserProfile(UserProfileBase):
    id: str = Field(..., description="Unique ID of the user")  # Unique identifier for the user
    is_deleted: bool = Field(..., description="Indicates if the user has been deleted")  # Soft delete flag
    
    class Config:
        from_attributes = True  # Allows the model to be populated from attributes