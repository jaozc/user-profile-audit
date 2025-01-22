from fastapi import APIRouter, HTTPException, status
from app.models.audit_event import AuditEvent, AuditEventAction
from app.models.user_profile import UserProfile, UserProfileCreate
from typing import List
import uuid
from app.database import connect_to_db, close_db_connection
import json
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.audit_event_repository import AuditEventRepository

# Initialize the API router
router = APIRouter()

# ===========================
# User Profile Management
# ===========================

@router.post("/users/profile/", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def create_user_profile(profile: UserProfileCreate):
    """
    Create a new user profile.

    Args:
        profile (UserProfileCreate): The profile data to create.

    Returns:
        UserProfile: The created user profile.
    """
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)
    
    new_profile = await user_profile_repo.create(profile)
    
    await connection.close()  # Close the connection after use
    return new_profile

@router.put("/users/{user_id}/profile/", response_model=UserProfile)
async def update_user_profile(user_id: str, profile: UserProfileCreate):
    """
    Update an existing user profile.

    Args:
        user_id (str): The ID of the user profile to update.
        profile (UserProfileCreate): The updated profile data.

    Returns:
        UserProfile: The updated user profile.
    """
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)
    
    updated_profile = await user_profile_repo.update(UserProfile(
        id=user_id,
        name=profile.name,
        email=profile.email,
        is_deleted=False  # Assuming the profile is not deleted
    ))

    await connection.close()  # Close the connection after use
    return updated_profile

@router.get("/users/{user_id}/profile/", response_model=UserProfile)
async def get_user_profile(user_id: str):
    """
    Retrieve a user profile by its ID.

    Args:
        user_id (str): The ID of the user profile to retrieve.

    Returns:
        UserProfile: The requested user profile.
    """
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)
    
    user_profile = await user_profile_repo.get_by_id(user_id)
    
    await connection.close()  # Close the connection after use
    
    if user_profile is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_profile.is_deleted:
        raise HTTPException(status_code=404, detail="User deleted")
    
    return user_profile

@router.get("/users/profile/", response_model=List[UserProfile])
async def get_users_profiles():
    """
    Retrieve all user profiles.

    Returns:
        List[UserProfile]: A list of all user profiles.
    """
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)
    
    user_profiles = await user_profile_repo.get_all()  # Implement this method in the repository
    
    await connection.close()  # Close the connection after use
    
    return user_profiles

@router.delete("/users/{user_id}/profile/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_profile(user_id: str):
    """
    Delete a user profile by its ID.

    Args:
        user_id (str): The ID of the user profile to delete.
    """
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)
    
    await user_profile_repo.delete(user_id)  # The delete method already logs the audit event

    await connection.close()  # Close the connection after use

@router.get("/users/profiles/active/", response_model=List[UserProfile])
async def get_active_user_profiles():
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)
    
    # Obtém todos os perfis de usuário ativos
    active_profiles = await user_profile_repo.get_all_active()
    
    await connection.close()  # Fechar a conexão após o uso
    
    return active_profiles

@router.get("/users/profiles/", response_model=List[UserProfile])
async def get_all_user_profiles():
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)
    
    # Obtém todos os perfis de usuário
    all_profiles = await user_profile_repo.get_all_inactive()
    
    await connection.close()  # Fechar a conexão após o uso
    
    return all_profiles

@router.post("/audit/events/rollback/{audit_event_id}", status_code=status.HTTP_200_OK)
async def rollback_user_profile(audit_event_id: str):
    """
    Rollback a user profile to a previous state based on an audit event ID and create a new rollback audit event.

    Args:
        audit_event_id (str): The ID of the audit event that contains the rollback information.

    Returns:
        AuditEvent: The newly created rollback audit event.
    """
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)
    audit_event_repo = AuditEventRepository(connection)

    try:
        await user_profile_repo.rollback_changes_by_event_id(audit_event_id)
    except Exception as e:
        await connection.close()
        raise HTTPException(status_code=400, detail=str(e))

    await connection.close()  # Close the connection after use

    return {"message": "Rollback successful"}


@router.post("/users/{user_id}/profile/restore/", response_model=UserProfile)
async def restore_user_profile(user_id: str):
    """
    Restore a deleted user profile.

    Args:
        user_id (str): The ID of the user profile to restore.

    Returns:
        UserProfile: The restored user profile.
    """
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)

    user_profile = await user_profile_repo.get_by_id(user_id)
    if user_profile is None:
        await connection.close()
        raise HTTPException(status_code=404, detail="User not found")

    if not user_profile.is_deleted:
        await connection.close()
        raise HTTPException(status_code=400, detail="User is not deleted")

    updated_profile = await user_profile_repo.restore(user_profile.id)

    await connection.close()  # Close the connection after use
    return updated_profile

# ===========================
# Audit Event Management
# ===========================

@router.get("/audit/events/", response_model=List[AuditEvent])
async def get_audit_events():
    """
    Retrieve all audit events.

    Returns:
        List[AuditEvent]: A list of all audit events.
    """
    connection = await connect_to_db()
    audit_event_repo = AuditEventRepository(connection)
    
    rows = await audit_event_repo.get_all()  # Implement this method in the repository
    await connection.close()  # Close the connection after use
    
    return rows

@router.get("/audit/events/{user_id}", response_model=List[AuditEvent])
async def get_user_audit_events(user_id: str):
    """
    Retrieve all audit events associated with a specific user ID.

    Args:
        user_id (str): The ID of the user whose audit events should be retrieved.

    Returns:
        List[AuditEvent]: A list of audit events related to the user.
    """
    connection = await connect_to_db()
    audit_event_repo = AuditEventRepository(connection)
    
    rows = await audit_event_repo.get_by_user_id(user_id)
    await connection.close()  # Close the connection after use
    
    return rows