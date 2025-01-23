# Importing necessary modules from Pydantic for data validation
from pydantic import BaseModel
from typing import Optional

# User model representing the basic user information
class User(BaseModel):
    username: str  # The username of the user
    email: Optional[str] = None  # The email of the user, optional
    disabled: Optional[bool] = None  # Indicates if the user is disabled, optional

# UserInDB model that extends the User model to include a hashed password
class UserInDB(User):
    hashed_password: str  # The hashed password of the user
