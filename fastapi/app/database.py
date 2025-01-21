import asyncpg
from fastapi import FastAPI

DATABASE_URL = "postgresql://admin:admin@db/audit_db"  # Use o nome do serviço 'db'

async def connect_to_db():
    return await asyncpg.connect(DATABASE_URL)

async def close_db_connection(connection):
    await connection.close()
