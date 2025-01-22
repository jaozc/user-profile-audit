from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Optional
from enum import Enum

# Enum class to define the possible actions for audit events
class AuditEventAction(str, Enum):
    CREATE_PROFILE = "CREATE_PROFILE"  # Action for creating a user profile
    UPDATE_PROFILE = "UPDATE_PROFILE"  # Action for updating a user profile
    DELETE_PROFILE = "DELETE_PROFILE"  # Action for deleting a user profile
    ROLLBACK_DELETE = "ROLLBACK_DELETE"  # Action for rolling back a delete operation
    ROLLBACK_EVENT = "ROLLBACK_EVENT"  # Action for rolling back any event
    RESTORE_PROFILE = "RESTORE_PROFILE"  # Action for restoring a deleted user profile

# Base model for audit events, containing common attributes
class AuditEventBase(BaseModel):
    user_id: str  # ID of the user associated with the audit event
    action: AuditEventAction  # The action performed that triggered the audit event
    timestamp: datetime = datetime.now()  # Timestamp of when the event occurred
    resource: str  # The resource that the action was performed on
    details: Optional[str] = None  # Optional details about the event
    changes: Optional[Dict[str, dict]] = Field(
        None,
        description="Records changes in specific fields: {'field': {'old': old_value, 'new': new_value}}"
    ) 

# Model for creating a new audit event, inherits from AuditEventBase
class AuditEventCreate(AuditEventBase):
    pass  # No additional fields for creation

# Model representing a complete audit event with an ID
class AuditEvent(AuditEventBase):
    id: str = Field(..., description="Unique ID of the audit event")  # Unique identifier for the audit event

    class Config:
        from_attributes = True  # Allows the model to be populated from attributes