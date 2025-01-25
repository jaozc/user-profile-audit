from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.api import auth
from app.api.auth import get_current_user, get_current_active_user
from app.models.user import User, UserInDB
from app.models.audit_event import AuditEvent, AuditEventAction
from app.models.user_profile import UserProfile, UserProfileCreate
from typing import List, Annotated
from app.database import connect_to_db
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.audit_event_repository import AuditEventRepository
from app.repositories.user_repository import UserRepository
from app.api.auth import oauth2_scheme
# Initialize the API router
router = APIRouter()


# ===============================
# User Authentication Management
# ===============================

@router.get("/users/me/", tags=["User Authentication"])
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    """
    Retrieve the current user's information.

    Args:
        current_user: The current authenticated user.

    Returns:
        User: The current user's information.
    """
    return current_user

@router.post("/users/login/", tags=["User Authentication"])
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user and return an access token.

    Args:
        form_data: The form data containing the username and password.

    Returns:
        dict: A dictionary containing the access token and token type.

    Raises:
        HTTPException: If the username or password is invalid.
    """
    user_repo = UserRepository()  # Create an instance of the user repository
    user = await user_repo.get_user(form_data.username)  # Fetch user data from the repository

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    hashed_password = auth.fake_hash_password(form_data.password)  # Hash the provided password for comparison
    
    # Check if the hashed password matches the stored hashed password
    if not hashed_password == user.hashed_password: 
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Return the access token and token type if authentication is successful
    return {"access_token": user.username, "token_type": "bearer"}

# ===========================
# User Profile Management
# ===========================

@router.post("/users/profile/", response_model=UserProfile, status_code=status.HTTP_201_CREATED, tags=["User Profile"])
async def create_user_profile(profile: UserProfileCreate, current_user: User = Depends(get_current_user)):
    """
    Create a new user profile.

    Args:
        profile (UserProfileCreate): The profile data to create.
        current_user: The current authenticated user.

    Returns:
        UserProfile: The created user profile.
    """
    connection = await connect_to_db()  # Establish a database connection
    user_profile_repo = UserProfileRepository(connection)  # Create an instance of the user profile repository
    
    new_profile = await user_profile_repo.create(profile)  # Create the new user profile in the database
    
    await connection.close()  # Close the connection after use
    return new_profile

@router.get("/users/profile/", response_model=List[UserProfile], tags=["User Profile"])
async def get_users_profiles(current_user: User = Depends(get_current_user)):
    """
    Retrieve all user profiles.

    Returns:
        List[UserProfile]: A list of all user profiles.
    """
    connection = await connect_to_db()  # Establish a database connection
    user_profile_repo = UserProfileRepository(connection)  # Create an instance of the user profile repository
    
    user_profiles = await user_profile_repo.get_all()  # Fetch all user profiles from the database
    
    await connection.close()  # Close the connection after use
    return user_profiles

@router.get("/users/{user_id}/profile/", response_model=UserProfile, tags=["User Profile"])
async def get_user_profile(user_id: str, current_user: User = Depends(get_current_user)):
    """
    Retrieve a user profile by its ID.

    Args:
        user_id (str): The ID of the user profile to retrieve.

    Returns:
        UserProfile: The requested user profile.

    Raises:
        HTTPException: If the user profile is not found or is deleted.
    """
    connection = await connect_to_db()  # Establish a database connection
    user_profile_repo = UserProfileRepository(connection)  # Create an instance of the user profile repository
    
    user_profile = await user_profile_repo.get_by_id(user_id)  # Fetch the user profile by ID
    
    await connection.close()  # Close the connection after use
    
    if user_profile is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_profile.is_deleted:
        raise HTTPException(status_code=404, detail="User deleted")
    
    return user_profile

@router.put("/users/{user_id}/profile/", response_model=UserProfile, tags=["User Profile"])
async def update_user_profile(user_id: str, profile: UserProfileCreate, current_user: User = Depends(get_current_user)):
    """
    Update an existing user profile.

    Args:
        user_id (str): The ID of the user profile to update.
        profile (UserProfileCreate): The updated profile data.

    Returns:
        UserProfile: The updated user profile.
    """
    connection = await connect_to_db()  # Establish a database connection
    user_profile_repo = UserProfileRepository(connection)  # Create an instance of the user profile repository
    
    updated_profile = await user_profile_repo.update(UserProfile(
        id=user_id,
        name=profile.name,
        email=profile.email,
        is_deleted=False  # Assuming the profile is not deleted
    ))

    await connection.close()  # Close the connection after use
    return updated_profile

@router.delete("/users/{user_id}/profile/", status_code=status.HTTP_204_NO_CONTENT, tags=["User Profile"])
async def delete_user_profile(user_id: str, current_user: User = Depends(get_current_user)):
    """
    Delete a user profile by its ID.

    Args:
        user_id (str): The ID of the user profile to delete.
    """
    connection = await connect_to_db()  # Establish a database connection
    user_profile_repo = UserProfileRepository(connection)  # Create an instance of the user profile repository
    
    await user_profile_repo.delete(user_id)  # The delete method already logs the audit event

    await connection.close()  # Close the connection after use

@router.get("/users/profiles/active/", response_model=List[UserProfile], tags=["User Profile"])
async def get_active_user_profiles(current_user: User = Depends(get_current_user)):
    """
    Retrieve all active user profiles.

    Returns:
        List[UserProfile]: A list of active user profiles.
    """
    connection = await connect_to_db()  # Establish a database connection
    user_profile_repo = UserProfileRepository(connection)  # Create an instance of the user profile repository
    
    active_profiles = await user_profile_repo.get_all_active()  # Fetch all active user profiles from the database
    
    await connection.close()  # Close the connection after use
    return active_profiles


# ===========================
# Audit Event Management
# ===========================

@router.get("/audit/events/", response_model=List[AuditEvent], tags=["Audit Event"])
async def get_audit_events(current_user: User = Depends(get_current_user)):
    """
    Retrieve all audit events.

    Returns:
        List[AuditEvent]: A list of all audit events.
    """
    connection = await connect_to_db()  # Establish a database connection
    audit_event_repo = AuditEventRepository(connection)  # Create an instance of the audit event repository
    
    rows = await audit_event_repo.get_all()  # Fetch all audit events from the database
    await connection.close()  # Close the connection after use
    
    return rows

@router.get("/audit/events/{user_id}", response_model=List[AuditEvent], tags=["Audit Event"])
async def get_user_audit_events(user_id: str, current_user: User = Depends(get_current_user)):
    """
    Retrieve all audit events associated with a specific user ID.

    Args:
        user_id (str): The ID of the user whose audit events should be retrieved.

    Returns:
        List[AuditEvent]: A list of audit events related to the user.
    """
    connection = await connect_to_db()  # Establish a database connection
    audit_event_repo = AuditEventRepository(connection)  # Create an instance of the audit event repository
    
    rows = await audit_event_repo.get_by_user_id(user_id)  # Fetch audit events for the user
    await connection.close()  # Close the connection after use
    
    return rows

@router.post("/audit/events/rollback/{audit_event_id}", status_code=status.HTTP_200_OK, tags=["Audit Event"])
async def rollback_user_profile(audit_event_id: str, current_user: User = Depends(get_current_user)):
    """
    Rollback a user profile to a previous state based on an audit event ID and create a new rollback audit event.

    Args:
        audit_event_id (str): The ID of the audit event that contains the rollback information.

    Returns:
        dict: A message indicating the rollback was successful.
    """
    connection = await connect_to_db()  # Establish a database connection
    user_profile_repo = UserProfileRepository(connection)  # Create an instance of the user profile repository

    try:
        await user_profile_repo.rollback_changes_by_event_id(audit_event_id)  # Rollback changes based on the audit event ID
    except Exception as e:
        await connection.close()  # Close the connection in case of an error
        raise HTTPException(status_code=400, detail=str(e))

    await connection.close()  # Close the connection after use
    return {"message": "Rollback successful"}

@router.post("/users/{user_id}/profile/restore/", response_model=UserProfile, tags=["User Profile"])
async def restore_user_profile(user_id: str, current_user: User = Depends(get_current_user)):
    """
    Restore a deleted user profile.

    Args:
        user_id (str): The ID of the user profile to restore.

    Returns:
        UserProfile: The restored user profile.
    """
    connection = await connect_to_db()  # Establish a database connection
    user_profile_repo = UserProfileRepository(connection)  # Create an instance of the user profile repository

    user_profile = await user_profile_repo.get_by_id(user_id)  # Fetch the user profile by ID
    if user_profile is None:
        await connection.close()  # Close the connection if user not found
        raise HTTPException(status_code=404, detail="User not found")

    if not user_profile.is_deleted:
        await connection.close()  # Close the connection if user is not deleted
        raise HTTPException(status_code=400, detail="User is not deleted")

    updated_profile = await user_profile_repo.restore(user_profile.id)  # Restore the user profile

    await connection.close()  # Close the connection after use
    return updated_profile