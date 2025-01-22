import uuid
import asyncpg
from app.models.audit_event import AuditEvent, AuditEventAction
import json
from typing import List

from datetime import datetime

class AuditEventRepository:
    def __init__(self, connection):
        self.connection = connection

    async def create(self, audit_event: AuditEvent):
        """
        Creates a new audit event in the database.

        :param audit_event: Instance of AuditEvent containing the details of the event to be recorded.
        """
        changes_json = json.dumps(audit_event.changes)
        audit_event_id = str(uuid.uuid4())
        await self.connection.execute(
            "INSERT INTO audit_events (id, user_id, action, resource, details, changes) VALUES ($1, $2, $3, $4, $5, $6)",
            audit_event_id, audit_event.user_id, audit_event.action.value, audit_event.resource, audit_event.details, changes_json
        )

    async def get_by_user_id(self, user_id: str):
        """
        Retrieves all audit events associated with a specific user ID.

        :param user_id: ID of the user whose audit events should be retrieved.
        :return: List of audit events related to the user.
        """
        rows = await self.connection.fetch("SELECT * FROM audit_events WHERE user_id = $1", user_id)
        print(rows)
        return [AuditEvent(**{**row, "changes": json.loads(row["changes"]) if row["changes"] else {}, "id": row["id"]}) for row in rows]

    async def get_all(self) -> List[AuditEvent]:
        """
        Retrieves all audit events recorded in the database.

        :return: List of all audit events.
        """
        rows = await self.connection.fetch("SELECT * FROM audit_events")
        return [AuditEvent(**{**row, "changes": json.loads(row["changes"]) if row["changes"] else {}}) for row in rows]

    async def get_by_id(self, event_id: str):
        """
        Retrieves a specific audit event by its ID.

        :param event_id: ID of the audit event to be retrieved.
        :return: The audit event if found, otherwise None.
        """
        row = await self.connection.fetchrow("SELECT * FROM audit_events WHERE id = $1", event_id)
        if row:
            return AuditEvent(**{**row, "changes": json.loads(row["changes"]) if row["changes"] else {}})
        return None
