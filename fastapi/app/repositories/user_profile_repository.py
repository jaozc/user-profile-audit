import asyncpg
from app.models.user_profile import UserProfile, UserProfileCreate
import uuid
from typing import List
from fastapi import HTTPException
from datetime import datetime
from app.models.audit_event import AuditEvent, AuditEventAction, AuditEventBase
from app.repositories.audit_event_repository import AuditEventRepository

class UserProfileRepository:
    def __init__(self, connection):
        """Initializes the repository with a database connection."""
        self.connection = connection

    async def create(self, user_profile: UserProfileCreate) -> UserProfile:
        """Creates a new user profile in the database and logs an audit event.

        Args:
            user_profile (UserProfileCreate): Data for the new user profile.

        Returns:
            UserProfile: The created user profile.
        """
        user_id = str(uuid.uuid4())  # Generate a unique user ID
        await self.connection.execute(
            "INSERT INTO user_profiles (id, name, email, is_deleted) VALUES ($1, $2, $3, $4)",
            user_id, user_profile.name, user_profile.email, False  # Insert new user profile into the database
        )

        # Create an audit event for the profile creation
        new_event_audit = AuditEventBase(
            user_id=user_id,
            action=AuditEventAction.CREATE_PROFILE,
            resource="user_profile",
            details="User profile created.",
            changes={
                "name": {"old": None, "new": user_profile.name},
                "email": {"old": None, "new": user_profile.email}
            }
        )
        
        await self.create_audit_event(new_event_audit)  # Log the audit event
        return UserProfile(id=user_id, name=user_profile.name, email=user_profile.email, is_deleted=False)

    async def get_by_id(self, user_id: str) -> UserProfile:
        """Retrieves a user profile by its ID.

        Args:
            user_id (str): The ID of the user profile.

        Returns:
            UserProfile: The corresponding user profile or None if not found.
        """
        row = await self.connection.fetchrow("SELECT * FROM user_profiles WHERE id = $1", user_id)
        if row:
            return UserProfile(**row)  # Return the user profile if found
        return None  # Return None if not found

    async def update(self, user_profile: UserProfile) -> UserProfile:
        """Updates an existing user profile and logs an audit event.

        Args:
            user_profile (UserProfile): The user profile with updated data.

        Returns:
            UserProfile: The updated user profile.
        """
        old_user_profile = await self.get_by_id(user_profile.id)  # Fetch the existing user profile
        if not old_user_profile:
            raise HTTPException(status_code=404, detail="User profile not found.")  # Raise error if not found

        await self.connection.execute(
            "UPDATE user_profiles SET name = $1, email = $2 WHERE id = $3",
            user_profile.name, user_profile.email, user_profile.id  # Update the user profile in the database
        )

        # Create an audit event for the profile update
        new_event_audit = AuditEventBase(
            user_id=old_user_profile.id,
            action=AuditEventAction.UPDATE_PROFILE,
            resource="user_profile",
            details="User profile updated.",
            changes={
                "name": {"old": old_user_profile.name, "new": user_profile.name},
                "email": {"old": old_user_profile.email, "new": user_profile.email}
            }
        )
        await self.create_audit_event(new_event_audit)  # Log the audit event
        
        return user_profile  # Return the updated user profile

    async def delete(self, user_id: str):
        """Marks a user profile as deleted (soft delete).

        Args:
            user_id (str): The ID of the user profile to be marked as deleted.
        """
        await self.connection.execute("UPDATE user_profiles SET is_deleted = TRUE WHERE id = $1", user_id)  # Soft delete the user profile

        old_user_profile = await self.get_by_id(user_id)  # Fetch the existing user profile

        # Create an audit event for the profile deletion
        audit_event = AuditEventBase(
            user_id=user_id,
            action=AuditEventAction.DELETE_PROFILE,
            resource="user_profile",
            details="User profile deleted.",
            changes={
                "name": {"old": old_user_profile.name, "new": None},
                "email": {"old": old_user_profile.email, "new": None}
            }
        )
        await self.create_audit_event(audit_event)  # Log the audit event
    
    async def restore(self, user_id: str):
        """Restores a deleted user profile.

        Args:
            user_id (str): The ID of the user profile to be restored.
        """
        await self.connection.execute("UPDATE user_profiles SET is_deleted = FALSE WHERE id = $1", user_id)  # Restore the user profile

        user_profile = await self.get_by_id(user_id)  # Fetch the restored user profile

        # Create an audit event for the profile restoration
        audit_event = AuditEventBase(
            user_id=user_id,
            action=AuditEventAction.RESTORE_PROFILE,
            resource="user_profile",
            details="User profile restored.",
            changes={
                "name": {"old": None, "new": user_profile.name},
                "email": {"old": None, "new": user_profile.email}
            }
        )
        await self.create_audit_event(audit_event)  # Log the audit event

        return user_profile  # Return the restored user profile

    async def get_all(self) -> List[UserProfile]:
        """Retrieves all user profiles from the database.

        Returns:
            List[UserProfile]: A list of all user profiles.
        """
        rows = await self.connection.fetch("SELECT * FROM user_profiles")  # Fetch all user profiles
        return [UserProfile(**row) for row in rows]  # Return a list of user profiles

    async def get_all_active(self) -> List[UserProfile]:
        """Retrieves all user profiles that are not deleted.

        Returns:
            List[UserProfile]: A list of active user profiles.
        """
        rows = await self.connection.fetch("SELECT * FROM user_profiles WHERE is_deleted = FALSE")  # Fetch active user profiles
        return [UserProfile(**row) for row in rows]  # Return a list of active user profiles

    async def get_all_inactive(self) -> List[UserProfile]:
        """Retrieves all user profiles, including deleted ones.

        Returns:
            List[UserProfile]: A list of all user profiles.
        """
        rows = await self.connection.fetch("SELECT * FROM user_profiles")  # Fetch all user profiles
        return [UserProfile(**row) for row in rows]  # Return a list of all user profiles

    async def create_audit_event(self, new_audit_event: AuditEvent):
        """Creates an audit event in the audit event repository.

        Args:
            new_audit_event (AuditEvent): The audit event to be created.
        """
        audit_event_repo = AuditEventRepository(self.connection)  # Initialize the audit event repository
        await audit_event_repo.create(audit_event=new_audit_event)  # Create the audit event

    async def rollback_changes_by_event_id(self, audit_event_id: str):
        """
        Rolls back an audit event by its ID, restoring the previous state of the affected user profile.

        Args:
            audit_event_id (str): ID of the audit event to be rolled back.
        """
        audit_event_repo = AuditEventRepository(self.connection)  # Initialize the audit event repository
        audit_event = await audit_event_repo.get_by_id(audit_event_id)  # Fetch the audit event
        
        if not audit_event:
            raise HTTPException(status_code=404, detail="Audit event not found.")  # Raise error if not found
        
        user_profile = await self.get_by_id(audit_event.user_id)  # Fetch the affected user profile
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found.")  # Raise error if not found
        
        if audit_event.action == AuditEventAction.DELETE_PROFILE:
            # Rollback the deletion
            await self.restore(user_profile.id)  # Use restore to restore the user profile
            
            # Create an audit event for the rollback
            rollback_event = AuditEventBase(
                user_id=user_profile.id,
                action=AuditEventAction.ROLLBACK_DELETE,
                timestamp=datetime.now(),
                resource="user_profile",
                details=f"Rolled back deletion for user profile ID: {user_profile.id}",
                changes={
                    "name": {'old': None, 'new': user_profile.name},
                    "email": {'old': None, 'new': user_profile.email},
                }
            )
            await self.create_audit_event(rollback_event)  # Log the rollback event
        else:
            # Rollback all field changes
            changes = audit_event.changes  # Get the changes from the audit event
            rollback_changes = {}  # Dictionary to store changes that will be recorded
            
            for field_name, change in changes.items():  # Iterate over each field and its changes
                old_value = change['old']  # Get the old value of the field
                current_value = getattr(user_profile, field_name)  # Get the current value of the field
                
                # Check if the old value is different from the current value
                if old_value != current_value:
                    setattr(user_profile, field_name, old_value)  # Set the old value for the specific field
                    rollback_changes[field_name] = {
                        'old': current_value,
                        'new': old_value
                    }
            
            # Update the user profile in the database
            await self.connection.execute(
                "UPDATE user_profiles SET name = $1, email = $2 WHERE id = $3",
                user_profile.name, user_profile.email, user_profile.id
            )
            
            # Create an audit event for the rollback if there are changes
            if rollback_changes:
                rollback_event = AuditEventBase(
                    user_id=user_profile.id,
                    action=AuditEventAction.ROLLBACK_EVENT,
                    timestamp=datetime.now(),
                    resource="user_profile",
                    details=f"Rolled back fields to previous values from audit event ID: {audit_event_id}",
                    changes=rollback_changes
                )
                await self.create_audit_event(rollback_event)  # Log the rollback event