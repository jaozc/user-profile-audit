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

    yield connection  # Permite que os testes sejam executados
    
    await close_db_connection(connection) 
