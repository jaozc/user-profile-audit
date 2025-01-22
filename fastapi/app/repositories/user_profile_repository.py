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
        user_id = str(uuid.uuid4())
        await self.connection.execute(
            "INSERT INTO user_profiles (id, name, email, is_deleted) VALUES ($1, $2, $3, $4)",
            user_id, user_profile.name, user_profile.email, False
        )

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
        
        await self.create_audit_event(new_event_audit)
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
            return UserProfile(**row)
        return None

    async def update(self, user_profile: UserProfile) -> UserProfile:
        """Updates an existing user profile and logs an audit event.

        Args:
            user_profile (UserProfile): The user profile with updated data.

        Returns:
            UserProfile: The updated user profile.
        """
        old_user_profile = await self.get_by_id(user_profile.id)
        if not old_user_profile:
            raise HTTPException(status_code=404, detail="User profile not found.")

        await self.connection.execute(
            "UPDATE user_profiles SET name = $1, email = $2 WHERE id = $3",
            user_profile.name, user_profile.email, user_profile.id
        )

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
        await self.create_audit_event(new_event_audit)
        
        return user_profile

    async def delete(self, user_id: str):
        """Marks a user profile as deleted (soft delete).

        Args:
            user_id (str): The ID of the user profile to be marked as deleted.
        """
        await self.connection.execute("UPDATE user_profiles SET is_deleted = TRUE WHERE id = $1", user_id)

        old_user_profile = await self.get_by_id(user_id)

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
        await self.create_audit_event(audit_event)
    
    async def restore(self, user_id: str):
        """Restores a deleted user profile.

        Args:
            user_id (str): The ID of the user profile to be restored.
        """
        await self.connection.execute("UPDATE user_profiles SET is_deleted = FALSE WHERE id = $1", user_id)

        user_profile = await self.get_by_id(user_id)

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
        await self.create_audit_event(audit_event)

        return user_profile

    async def get_all(self) -> List[UserProfile]:
        """Retrieves all user profiles from the database.

        Returns:
            List[UserProfile]: A list of all user profiles.
        """
        rows = await self.connection.fetch("SELECT * FROM user_profiles")
        return [UserProfile(**row) for row in rows]

    async def get_all_active(self) -> List[UserProfile]:
        """Retrieves all user profiles that are not deleted.

        Returns:
            List[UserProfile]: A list of active user profiles.
        """
        rows = await self.connection.fetch("SELECT * FROM user_profiles WHERE is_deleted = FALSE")
        return [UserProfile(**row) for row in rows]

    async def get_all_inactive(self) -> List[UserProfile]:
        """Retrieves all user profiles, including deleted ones.

        Returns:
            List[UserProfile]: A list of all user profiles.
        """
        rows = await self.connection.fetch("SELECT * FROM user_profiles")
        return [UserProfile(**row) for row in rows]

    async def create_audit_event(self, new_audit_event: AuditEvent):
        """Creates an audit event in the audit event repository.

        Args:
            new_audit_event (AuditEvent): The audit event to be created.
        """
        audit_event_repo = AuditEventRepository(self.connection)
        await audit_event_repo.create(audit_event=new_audit_event)

    async def rollback_changes_by_event_id(self, audit_event_id: str):
        """
        Rolls back an audit event by its ID, restoring the previous state of the affected user profile.

        :param audit_event_id: ID of the audit event to be rolled back.
        """
        audit_event_repo = AuditEventRepository(self.connection)
        audit_event = await audit_event_repo.get_by_id(audit_event_id)
        
        if not audit_event:
            raise HTTPException(status_code=404, detail="Audit event not found.")
        
        user_profile = await self.get_by_id(audit_event.user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found.")
        
        if audit_event.action == AuditEventAction.DELETE_PROFILE:
            # Rollback the deletion
            user_profile.is_deleted = False
            await self.update(user_profile)
            
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
            await self.create_audit_event(rollback_event)
        else:
            # Rollback all field changes
            changes = audit_event.changes
            for field_name, change in changes.items():
                old_value = change['old']
                setattr(user_profile, field_name, old_value)  # Set the old value for the specific field
            
            await self.update(user_profile)  # Update the user profile in the database
            
            # Create an audit event for the rollback
            rollback_event = AuditEventBase(
                user_id=user_profile.id,
                action=AuditEventAction.ROLLBACK_EVENT,
                timestamp=datetime.now(),
                resource="user_profile",
                details=f"Rolled back fields to previous values from audit event ID: {audit_event_id}",
                changes={field_name: {'old': old_value, 'new': getattr(user_profile, field_name)} for field_name, change in changes.items()}
            )
            await self.create_audit_event(rollback_event)
        