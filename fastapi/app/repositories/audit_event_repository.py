import asyncpg
from app.models.audit_event import AuditEvent
import json
from typing import List

class AuditEventRepository:
    def __init__(self, connection):
        self.connection = connection

    async def create(self, audit_event: AuditEvent):
        changes_json = json.dumps(audit_event.changes)
        await self.connection.execute(
            "INSERT INTO audit_events (user_id, action, resource, details, changes) VALUES ($1, $2, $3, $4, $5)",
            audit_event.user_id, audit_event.action, audit_event.resource, audit_event.details, changes_json
        )

    async def get_by_user_id(self, user_id: str):
        rows = await self.connection.fetch("SELECT * FROM audit_events WHERE user_id = $1", user_id)
        return [AuditEvent(**{**row, "changes": json.loads(row["changes"]) if row["changes"] else {}}) for row in rows]

    async def get_all(self) -> List[AuditEvent]:
        rows = await self.connection.fetch("SELECT * FROM audit_events")
        return [AuditEvent(**{**row, "changes": json.loads(row["changes"]) if row["changes"] else {}}) for row in rows]
