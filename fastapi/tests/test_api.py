import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bem-vindo à API de Auditoria de Usuários!"}

def test_create_user_profile():
    profile_data = {
        "name": "John Doe",
        "email": "john.doe@example.com"
    }
    response = client.post("/api/v1/users/profile/", json=profile_data)
    assert response.status_code == 201
    assert response.json()["name"] == profile_data["name"]
    assert response.json()["email"] == profile_data["email"]
    assert "id" in response.json()
    assert response.json()["id"] is not None

def test_update_user_profile():
    # Primeiro cria um perfil
    profile_data = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data)
    user_id = create_response.json()["id"]
    
    # Atualiza o perfil
    updated_data = {
        "name": "Jane Smith",
        "email": "jane.smith@example.com"
    }
    update_response = client.put(f"/api/v1/users/{user_id}/profile/", json=updated_data)
    assert update_response.status_code == 200
    assert update_response.json()["name"] == updated_data["name"]
    
    # Verifica se a auditoria registrou a mudança
    audit_response = client.get(f"/api/v1/audit/events/{user_id}")
    assert audit_response.status_code == 200
    events = audit_response.json()
    assert len(events) == 2  # Deve ter 2 eventos: criação e atualização
    assert events[-1]["action"] == "UPDATE_PROFILE"
    assert "changes" in events[-1]

def test_get_user_profile():
    # Primeiro cria um perfil
    profile_data = {
        "name": "Test User",
        "email": "test@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data)
    user_id = create_response.json()["id"]
    
    # Busca o perfil
    get_response = client.get(f"/api/v1/users/{user_id}/profile/")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == profile_data["name"]

def test_create_audit_event():
    event = {
        "user_id": "user123",
        "action": "LOGIN",
        "resource": "auth_system",
        "details": "Login successful",
        "timestamp": datetime.now().isoformat()
    }
    response = client.post("/api/v1/audit/events/", json=event)
    assert response.status_code == 201
    assert response.json()["user_id"] == event["user_id"]
    assert response.json()["action"] == event["action"]

def test_get_audit_events():
    response = client.get("/api/v1/audit/events/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_get_user_audit_events():
    # Primeiro, cria um evento para o usuário
    event = {
        "user_id": "test_user",
        "action": "UPDATE_PROFILE",
        "resource": "user_profile",
        "details": "Updated email",
        "timestamp": datetime.now().isoformat()
    }
    client.post("/api/v1/audit/events/", json=event)
    
    # Busca eventos do usuário
    response = client.get("/api/v1/audit/events/test_user")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0
    assert response.json()[0]["user_id"] == "test_user"
