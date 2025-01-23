import asyncpg  # Importing asyncpg for asynchronous PostgreSQL database interaction
from app.models.user import User, UserInDB  # Importing User and UserInDB models from the user module
from fastapi import HTTPException  # Importing HTTPException for handling HTTP errors

# A fake database for demonstration purposes, simulating user data storage
fake_users_db = {
    "test": {
        "username": "test",
        "email": "test@example.com",
        "hashed_password": "fakehashedsecret",  # Fake hashed password for the user
        "disabled": False,  # Indicates if the user account is disabled
    },
    "joaocosta": {
        "username": "joaocosta",
        "email": "joaocosta@example.com",
        "hashed_password": "fakehashedsecret",  # Fake hashed password for the user
        "disabled": False,  # Indicates if the user account is disabled
    },
}

class UserRepository:
    def __init__(self):
        """Initializes the UserRepository class."""
        pass

    def get_user(self, username: str) -> UserInDB:
        """
        Retrieves a user from the fake database by username.

        :param username: The username of the user to retrieve.
        :return: An instance of UserInDB if the user exists, otherwise None.
        """
        if username in fake_users_db:  # Check if the username exists in the fake database
            user_dict = fake_users_db[username]  # Retrieve user data
            return UserInDB(**user_dict)  # Return an instance of UserInDB populated with user data
        return None  # Return None if the user does not exist
