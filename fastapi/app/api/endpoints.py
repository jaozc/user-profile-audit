from fastapi import APIRouter, HTTPException, status
from app.models.audit_event import AuditEvent
from app.models.user_profile import UserProfile, UserProfileCreate
from typing import List
import uuid
from app.database import connect_to_db, close_db_connection
import json
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.audit_event_repository import AuditEventRepository

router = APIRouter()

@router.post("/users/profile/", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def create_user_profile(profile: UserProfileCreate):
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)
    
    new_profile = await user_profile_repo.create(profile)
    
    # Registra evento de auditoria para criação de perfil
    audit_event = AuditEvent(
        user_id=new_profile.id,
        action="CREATE_PROFILE",
        resource="user_profile",
        details=f"Perfil criado para {profile.name}",
        changes={
            "name": {"old": None, "new": profile.name},
            "email": {"old": None, "new": profile.email}
        }
    )
    
    audit_event_repo = AuditEventRepository(connection)
    await audit_event_repo.create(audit_event)
    
    await connection.close()  # Fechar a conexão após o uso
    return new_profile

@router.put("/users/{user_id}/profile/", response_model=UserProfile)
async def update_user_profile(user_id: str, profile: UserProfileCreate):
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)
    
    # Verifica se o usuário existe
    old_profile = await user_profile_repo.get_by_id(user_id)
    if old_profile is None:
        await connection.close()
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    changes = {}
    
    # Detecta mudanças nos campos
    if old_profile.name != profile.name:
        changes["name"] = {"old": old_profile.name, "new": profile.name}
    if old_profile.email != profile.email:
        changes["email"] = {"old": old_profile.email, "new": profile.email}
    
    # Atualiza o perfil
    updated_profile = await user_profile_repo.update(UserProfile(
        id=user_id,
        name=profile.name,
        email=profile.email,
        is_deleted=old_profile.is_deleted  # Include is_deleted from old_profile
    ))
    
    # Registra evento de auditoria para atualização
    if changes:
        audit_event = AuditEvent(
            user_id=user_id,
            action="UPDATE_PROFILE",
            resource="user_profile",
            details="Perfil atualizado",
            changes=changes
        )

        audit_event_repo = AuditEventRepository(connection)
        await audit_event_repo.create(audit_event)
    
    await connection.close()  # Fechar a conexão após o uso
    
    return updated_profile

@router.get("/users/{user_id}/profile/", response_model=UserProfile)
async def get_user_profile(user_id: str):
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)
    
    # Obtém o perfil do usuário usando o repositório
    user_profile = await user_profile_repo.get_by_id(user_id)
    
    await connection.close()  # Fechar a conexão após o uso
    
    if user_profile is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if user_profile.is_deleted:
        raise HTTPException(status_code=404, detail="Usuário deletado")
    
    return user_profile

@router.get("/users/profile/", response_model=List[UserProfile])
async def get_users_profiles():
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)
    
    # Obtém todos os perfis de usuário usando o repositório
    user_profiles = await user_profile_repo.get_all()  # Você precisará implementar esse método no repositório
    
    await connection.close()  # Fechar a conexão após o uso
    
    return user_profiles

@router.post("/audit/events/", response_model=AuditEvent, status_code=status.HTTP_201_CREATED)
async def create_audit_event(event: AuditEvent):
    connection = await connect_to_db()
    audit_event_repo = AuditEventRepository(connection)
    
    await audit_event_repo.create(event)  # Usando o repositório para criar o evento de auditoria
    
    await connection.close()  # Fechar a conexão após o uso
    return event

@router.get("/audit/events/", response_model=List[AuditEvent])
async def get_audit_events():
    connection = await connect_to_db()
    audit_event_repo = AuditEventRepository(connection)
    
    rows = await audit_event_repo.get_all()  # Você precisará implementar esse método no repositório
    await connection.close()  # Fechar a conexão após o uso
    
    return rows

@router.get("/audit/events/{user_id}", response_model=List[AuditEvent])
async def get_user_audit_events(user_id: str):
    connection = await connect_to_db()
    audit_event_repo = AuditEventRepository(connection)
    
    rows = await audit_event_repo.get_by_user_id(user_id)
    await connection.close()  # Fechar a conexão após o uso
    
    return rows

@router.delete("/users/{user_id}/profile/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_profile(user_id: str):
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)
    
    # Verifica se o usuário existe
    old_profile = await user_profile_repo.get_by_id(user_id)
    if old_profile is None or old_profile.is_deleted:
        await connection.close()
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Realiza o soft delete
    await user_profile_repo.soft_delete(user_id)

    # Registra evento de auditoria para a exclusão
    audit_event = AuditEvent(
        user_id=user_id,
        action="DELETE_PROFILE",
        resource="user_profile",
        details=f"Perfil deletado para {old_profile.name}",
        changes={
            "name": {"old": old_profile.name, "new": None},
            "email": {"old": old_profile.email, "new": None}
        }
    )
    
    audit_event_repo = AuditEventRepository(connection)
    await audit_event_repo.create(audit_event)

    await connection.close()  # Fechar a conexão após o uso

@router.get("/users/profiles/active/", response_model=List[UserProfile])
async def get_active_user_profiles():
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)
    
    # Obtém todos os perfis de usuário ativos
    active_profiles = await user_profile_repo.get_all_active()
    
    await connection.close()  # Fechar a conexão após o uso
    
    return active_profiles

@router.get("/users/profiles/", response_model=List[UserProfile])
async def get_all_user_profiles():
    connection = await connect_to_db()
    user_profile_repo = UserProfileRepository(connection)
    
    # Obtém todos os perfis de usuário
    all_profiles = await user_profile_repo.get_all_inactive()
    
    await connection.close()  # Fechar a conexão após o uso
    
    return all_profiles