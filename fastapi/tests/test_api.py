import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime
from app.models.audit_event import AuditEventAction

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bem-vindo à API de Auditoria de Usuários!"}

@pytest.mark.asyncio
async def test_create_user_profile(db_setup):
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

@pytest.mark.asyncio
async def test_update_user_profile(db_setup):
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
    assert events[-1]["action"] == AuditEventAction.UPDATE_PROFILE.value
    assert "changes" in events[-1]

@pytest.mark.asyncio
async def test_get_user_profile(db_setup):
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

@pytest.mark.asyncio
async def test_create_audit_event(db_setup):
    # Cria um perfil de usuário
    profile_data = {
        "name": "User for Audit",
        "email": "audit.user@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data)
    user_id = create_response.json()["id"]

    # Verifica se o perfil foi criado com sucesso
    assert create_response.status_code == 201
    assert create_response.json()["name"] == profile_data["name"]

    # Verifica se o evento de auditoria foi criado para a criação do perfil
    audit_response = client.get(f"/api/v1/audit/events/{user_id}")
    assert audit_response.status_code == 200
    events = audit_response.json()
    assert len(events) > 0
    assert events[-1]["action"] == AuditEventAction.CREATE_PROFILE.value
    assert events[-1]["user_id"] == user_id
    assert events[-1]["details"] == f"User profile created."

@pytest.mark.asyncio
async def test_get_audit_events(db_setup):
    response = client.get("/api/v1/audit/events/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_get_user_audit_events(db_setup):
    # Primeiro, cria um perfil de usuário
    profile_data = {
        "name": "User for Audit 2",
        "email": "audit.user2@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data)
    user_id = create_response.json()["id"]

    # Verifica se o perfil foi criado com sucesso
    assert create_response.status_code == 201
    assert create_response.json()["name"] == profile_data["name"]

    # Atualiza os dados do usuário duas vezes
    update_data_1 = {
        "name": "Updated User Name",
        "email": "updated.user2@example.com"
    }
    update_response_1 = client.put(f"/api/v1/users/{user_id}/profile", json=update_data_1)
    assert update_response_1.status_code == 200

    update_data_2 = {
        "name": "Another Update",
        "email": "another.update2@example.com"
    }
    update_response_2 = client.put(f"/api/v1/users/{user_id}/profile", json=update_data_2)
    assert update_response_2.status_code == 200

    # Busca todos os eventos de auditoria do usuário
    response = client.get(f"/api/v1/audit/events/{user_id}")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) > 0

    # Verifica se os eventos de auditoria correspondem às atualizações
    assert any(event["action"] == AuditEventAction.UPDATE_PROFILE.value for event in events)
    assert any(event["user_id"] == user_id for event in events)

@pytest.mark.asyncio
async def test_delete_user_profile(db_setup):
    # Primeiro cria um perfil
    profile_data = {
        "name": "John Field",
        "email": "john.field@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data)
    user_id = create_response.json()["id"]
    
    # Deleta o perfil
    delete_response = client.delete(f"/api/v1/users/{user_id}/profile/")
    assert delete_response.status_code == 204
    
    # Verifica se o perfil foi marcado como deletado
    get_response = client.get(f"/api/v1/users/{user_id}/profile/")
    assert get_response.status_code == 404  # O perfil não deve ser encontrado

    # Verifica se o evento de auditoria foi criado
    audit_response = client.get(f"/api/v1/audit/events/{user_id}")
    assert audit_response.status_code == 200
    events = audit_response.json()
    assert len(events) > 0
    assert events[-1]["action"] == AuditEventAction.DELETE_PROFILE.value
    assert events[-1]["details"] == f"User profile deleted."

@pytest.mark.asyncio
async def test_get_active_user_profiles(db_setup):
    # Primeiro cria um perfil
    profile_data = {
        "name": "Active User",
        "email": "active.user@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data)
    user_id = create_response.json()["id"]  # Armazena o user_id

    # Deleta o perfil
    delete_response = client.delete(f"/api/v1/users/{user_id}/profile/")
    assert delete_response.status_code == 204

    # Obtém perfis ativos
    active_response = client.get("/api/v1/users/profiles/active/")
    assert active_response.status_code == 200
    active_profiles = active_response.json()
    assert len(active_profiles) == 5  # Deve retornar apenas perfis não deletados

@pytest.mark.asyncio
async def test_get_all_user_profiles(db_setup):
    # Obtém todos os perfis
    all_response = client.get("/api/v1/users/profiles/")
    assert all_response.status_code == 200
    all_profiles = all_response.json()
    assert isinstance(all_profiles, list)  # Deve retornar uma lista

@pytest.mark.asyncio
async def test_get_deleted_user_profile(db_setup):
    # Primeiro cria um perfil
    profile_data = {
        "name": "Deleted User",
        "email": "deleted.user@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data)
    user_id = create_response.json()["id"]

    # Deleta o perfil
    client.delete(f"/api/v1/users/{user_id}/profile/")

    # Tenta obter o perfil deletado
    deleted_response = client.get(f"/api/v1/users/{user_id}/profile/")
    assert deleted_response.status_code == 404
    assert deleted_response.json() == {"detail": "User deleted"}

@pytest.mark.asyncio
async def test_restore_deleted_user_profile(db_setup):
    # Primeiro, cria um perfil
    profile_data = {
        "name": "User to Restore",
        "email": "restore.user@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data)
    user_id = create_response.json()["id"]

    # Deleta o perfil
    delete_response = client.delete(f"/api/v1/users/{user_id}/profile/")
    assert delete_response.status_code == 204

    # Verifica se o perfil foi marcado como deletado
    get_response = client.get(f"/api/v1/users/{user_id}/profile/")
    assert get_response.status_code == 404  # O perfil não deve ser encontrado

    # Restaura o perfil
    restore_response = client.post(f"/api/v1/users/{user_id}/profile/restore/")  # Verifique se o endpoint está correto
    assert restore_response.status_code == 200
    assert restore_response.json()["is_deleted"] is False

    # Verifica se o perfil foi restaurado
    restored_profile = client.get(f"/api/v1/users/{user_id}/profile/")
    assert restored_profile.status_code == 200
    assert restored_profile.json()["name"] == profile_data["name"]

@pytest.mark.asyncio
async def test_change_and_rollback_user_profile(db_setup):
    # Create a user profile
    profile_data = {
        "name": "User to Change And Rollback",
        "email": "change.user.rollback@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data)
    user_id = create_response.json()["id"]

    # Update the user profile
    updated_data = {
        "name": "Changed User",
        "email": "changed.user.rollback@example.com"
    }
    update_response = client.put(f"/api/v1/users/{user_id}/profile/", json=updated_data)
    assert update_response.status_code == 200

    # Verifica se as alterações foram aplicadas
    updated_profile = client.get(f"/api/v1/users/{user_id}/profile/")
    assert updated_profile.json()["name"] == updated_data["name"]

    audit_event = client.get(f"/api/v1/audit/events/{user_id}")
    assert audit_event.status_code == 200
    
    # Verifique se a resposta é uma lista e obtenha o primeiro evento
    events = audit_event.json()
    assert isinstance(events, list)
    assert len(events) > 0
    audit_event_id = events[1]["id"]

    # Restaure as alterações usando o endpoint correto
    rollback_response = client.post(f"/api/v1/audit/events/rollback/{audit_event_id}")  # Use o ID de evento de auditoria válido
    assert rollback_response.status_code == 200

    # Verifique se as alterações foram revertidas
    rolled_back_profile = client.get(f"/api/v1/users/{user_id}/profile/")
    assert rolled_back_profile.json()["name"] == profile_data["name"]
    assert rolled_back_profile.json()["email"] == profile_data["email"]

@pytest.mark.asyncio
async def test_audit_event_creation_on_delete(db_setup):
    # Primeiro cria um perfil
    profile_data = {
        "name": "User for Audit Creation",
        "email": "audit.user.creation@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data)
    user_id = create_response.json()["id"]

    # Deleta o perfil
    delete_response = client.delete(f"/api/v1/users/{user_id}/profile/")
    assert delete_response.status_code == 204

    # Verifica se o evento de auditoria foi criado
    audit_response = client.get(f"/api/v1/audit/events/{user_id}")
    assert audit_response.status_code == 200
    events = audit_response.json()
    assert len(events) > 0
    assert events[-1]["action"] == AuditEventAction.DELETE_PROFILE.value
    assert events[-1]["details"] == f"User profile deleted."
