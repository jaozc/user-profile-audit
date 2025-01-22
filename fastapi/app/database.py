import asyncpg
from fastapi import FastAPI

# Database connection URL
DATABASE_URL = "postgresql://admin:admin@db/audit_db"  # Use the service name 'db'

async def connect_to_db():
    """
    Establish a connection to the PostgreSQL database.

    Returns:
        asyncpg.Connection: A connection object to interact with the database.
    """
    return await asyncpg.connect(DATABASE_URL)

async def close_db_connection(connection):
    """
    Close the given database connection.

    Args:
        connection (asyncpg.Connection): The connection object to be closed.
    """
    await connection.close()
