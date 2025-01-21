import sys
import os
from pathlib import Path
import pytest
from app.database import connect_to_db, close_db_connection
import json

# Adiciona o diretório raiz do projeto ao PYTHONPATH
root_dir = str(Path(__file__).parent.parent)
sys.path.append(root_dir)

@pytest.fixture(scope="function")
async def db_setup():
    connection = await connect_to_db()
    await connection.execute("BEGIN;")  # Inicia uma transação

    # Limpa as tabelas antes de cada teste
    await connection.execute("DELETE FROM user_profiles;")
    await connection.execute("DELETE FROM audit_events;")

    yield connection  # Permite que os testes sejam executados
    
    await connection.execute("ROLLBACK;")  # Reverte a transação
    await close_db_connection(connection) 

async def create_audit_event(connection, user_id, action, resource, details, changes):
    changes_json = json.dumps(changes)  # Converte o dicionário para uma string JSON
    await connection.execute(
        "INSERT INTO audit_events (user_id, action, resource, details, changes) VALUES ($1, $2, $3, $4, $5)",
        user_id, action, resource, details, changes_json
    ) 