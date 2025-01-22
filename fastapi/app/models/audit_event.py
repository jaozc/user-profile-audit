from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Optional
from enum import Enum

class AuditEventAction(str, Enum):
    CREATE_PROFILE = "CREATE_PROFILE"
    UPDATE_PROFILE = "UPDATE_PROFILE"
    DELETE_PROFILE = "DELETE_PROFILE"
    ROLLBACK_DELETE = "ROLLBACK_DELETE"
    ROLLBACK_EVENT = "ROLLBACK_EVENT"
    RESTORE_PROFILE = "RESTORE_PROFILE"

class AuditEventBase(BaseModel):
    user_id: str
    action: AuditEventAction
    timestamp: datetime = datetime.now()
    resource: str
    details: str | None = None
    changes: Dict[str, dict] | None = Field(
        None,
        description="Registra alterações em campos específicos: {'field': {'old': old_value, 'new': new_value}}"
    ) 

class AuditEventCreate(AuditEventBase):
    pass

class AuditEvent(AuditEventBase):
    id: str = Field(..., description="ID único do evento de auditoria")

    class Config:
        from_attributes = True