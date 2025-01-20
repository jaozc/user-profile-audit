from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Optional

class AuditEvent(BaseModel):
    user_id: str
    action: str
    timestamp: datetime = datetime.now()
    resource: str
    details: str | None = None
    changes: Dict[str, dict] | None = Field(
        None,
        description="Registra alterações em campos específicos: {'field': {'old': old_value, 'new': new_value}}"
    ) 