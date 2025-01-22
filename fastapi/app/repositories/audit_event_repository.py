import uuid
import asyncpg
from app.models.audit_event import AuditEvent, AuditEventAction
import json
from typing import List
from datetime import datetime

class AuditEventRepository:
    def __init__(self, connection):
        """
        Initializes the AuditEventRepository with a database connection.

        :param connection: The database connection to be used for executing queries.
        """
        self.connection = connection

    async def create(self, audit_event: AuditEvent):
        """
        Creates a new audit event in the database.

        :param audit_event: Instance of AuditEvent containing the details of the event to be recorded.
        """
        # Convert changes to JSON format for storage
        changes_json = json.dumps(audit_event.changes)
        # Generate a unique ID for the new audit event
        audit_event_id = str(uuid.uuid4())
        # Insert the audit event into the database
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
        # Fetch all audit events for the specified user ID
        rows = await self.connection.fetch("SELECT * FROM audit_events WHERE user_id = $1", user_id)
        # Return a list of AuditEvent instances created from the fetched rows
        return [AuditEvent(**{**row, "changes": json.loads(row["changes"]) if row["changes"] else {}, "id": row["id"]}) for row in rows]

    async def get_all(self) -> List[AuditEvent]:
        """
        Retrieves all audit events recorded in the database.

        :return: List of all audit events.
        """
        # Fetch all audit events from the database
        rows = await self.connection.fetch("SELECT * FROM audit_events")
        # Return a list of AuditEvent instances created from the fetched rows
        return [AuditEvent(**{**row, "changes": json.loads(row["changes"]) if row["changes"] else {}}) for row in rows]

    async def get_by_id(self, event_id: str):
        """
        Retrieves a specific audit event by its ID.

        :param event_id: ID of the audit event to be retrieved.
        :return: The audit event if found, otherwise None.
        """
        # Fetch the audit event by its ID
        row = await self.connection.fetchrow("SELECT * FROM audit_events WHERE id = $1", event_id)
        if row:
            # Return an AuditEvent instance if found
            return AuditEvent(**{**row, "changes": json.loads(row["changes"]) if row["changes"] else {}})
        return None  # Return None if the event is not found
