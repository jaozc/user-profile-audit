# Import necessary modules and classes
from typing import Annotated
from fastapi import Depends, HTTPException, status
from app.models.user import User
from fastapi.security import OAuth2PasswordBearer
from app.repositories.user_repository import fake_users_db

# Create an instance of OAuth2PasswordBearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login/")

# Function to decode a token and retrieve the user associated with it
def fake_decode_token(token: str):
    from app.repositories.user_repository import UserRepository
    user_repository = UserRepository()  # Instantiate the UserRepository
    user = user_repository.get_user(token)  # Get user from the repository using the token
    return user

# Dependency that retrieves the current user based on the provided token
def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)  # Decode the token to get the user
    if not user:  # Check if the user is valid
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,  # Raise an error if the user is not valid
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user  # Return the valid user

# Dependency that checks if the current user is active
def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.disabled:  # Check if the user is disabled
        raise HTTPException(status_code=400, detail="Inactive user")  # Raise an error if the user is inactive
    return current_user  # Return the active user

# Function to fake decode a token for demonstration purposes
def fake_decode_token(token):
    return User(
        username=token + "fakedecoded", email="john@example.com"  # Return a fake user object
    )

# Function to fake hash a password for demonstration purposes
def fake_hash_password(password: str):
    return "fakehashed" + password  # Return a fake hashed password
