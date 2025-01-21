from fastapi import APIRouter, HTTPException, status
from app.models.audit_event import AuditEvent
from app.models.user_profile import UserProfile, UserProfileCreate
from typing import List
import uuid
from app.database import connect_to_db, close_db_connection
import json

router = APIRouter()

@router.post("/users/profile/", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def create_user_profile(profile: UserProfileCreate):
    connection = await connect_to_db()
    user_id = str(uuid.uuid4())
    new_profile = UserProfile(
        id=user_id,
        name=profile.name,
        email=profile.email
    )
    
    await connection.execute("INSERT INTO user_profiles (id, name, email) VALUES ($1, $2, $3)", user_id, profile.name, profile.email)
    
    # Registra evento de auditoria para criação de perfil
    audit_event = AuditEvent(
        user_id=user_id,
        action="CREATE_PROFILE",
        resource="user_profile",
        details=f"Perfil criado para {profile.name}",
        changes={
            "name": {"old": None, "new": profile.name},
            "email": {"old": None, "new": profile.email}
        }
    )
    
    # Converte o dicionário de mudanças para uma string JSON
    changes_json = json.dumps(audit_event.changes)
    
    await connection.execute("INSERT INTO audit_events (user_id, action, resource, details, changes) VALUES ($1, $2, $3, $4, $5)", 
                             user_id, audit_event.action, audit_event.resource, audit_event.details, changes_json)
    
    await close_db_connection(connection)
    
    return new_profile

@router.put("/users/{user_id}/profile/", response_model=UserProfile)
async def update_user_profile(user_id: str, profile: UserProfileCreate):
    connection = await connect_to_db()
    
    # Verifica se o usuário existe
    row = await connection.fetchrow("SELECT * FROM user_profiles WHERE id = $1", user_id)
    if row is None:
        await close_db_connection(connection)
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    old_profile = UserProfile(id=row['id'], name=row['name'], email=row['email'])
    changes = {}
    
    # Detecta mudanças nos campos
    if old_profile.name != profile.name:
        changes["name"] = {"old": old_profile.name, "new": profile.name}
    if old_profile.email != profile.email:
        changes["email"] = {"old": old_profile.email, "new": profile.email}
    
    # Atualiza o perfil
    await connection.execute("UPDATE user_profiles SET name = $1, email = $2 WHERE id = $3", profile.name, profile.email, user_id)
    
    # Registra evento de auditoria para atualização
    if changes:
        audit_event = AuditEvent(
            user_id=user_id,
            action="UPDATE_PROFILE",
            resource="user_profile",
            details="Perfil atualizado",
            changes=changes
        )

        changes_json = json.dumps(audit_event.changes)

        await connection.execute("INSERT INTO audit_events (user_id, action, resource, details, changes) VALUES ($1, $2, $3, $4, $5)", 
                                 user_id, audit_event.action, audit_event.resource, audit_event.details, changes_json)
    
    await close_db_connection(connection)
    
    return UserProfile(id=user_id, name=profile.name, email=profile.email)

@router.get("/users/{user_id}/profile/", response_model=UserProfile)
async def get_user_profile(user_id: str):
    connection = await connect_to_db()
    
    row = await connection.fetchrow("SELECT * FROM user_profiles WHERE id = $1", user_id)
    await close_db_connection(connection)
    
    if row is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return UserProfile(id=row['id'], name=row['name'], email=row['email'])

@router.get("/users/profile/", response_model=UserProfile)
async def get_users_profiles():
    connection = await connect_to_db()
    
    row = await connection.fetchrow("SELECT * FROM user_profiles ")
    await close_db_connection(connection)
    
    if row is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return UserProfile(id=row['id'], name=row['name'], email=row['email'])

# Mantém os endpoints existentes de auditoria
@router.post("/audit/events/", response_model=AuditEvent)
async def create_audit_event(event: AuditEvent, status_code=status.HTTP_201_CREATED):
    connection = await connect_to_db()
    await connection.execute("INSERT INTO audit_events (user_id, action, resource, details, changes) VALUES ($1, $2, $3, $4, $5)", 
                             event.user_id, event.action, event.resource, event.details, event.changes)
    await close_db_connection(connection)
    return event

@router.get("/audit/events/", response_model=List[AuditEvent])
async def get_audit_events():
    connection = await connect_to_db()
    rows = await connection.fetch("SELECT * FROM audit_events")
    await close_db_connection(connection)
    
    return [AuditEvent(**{**row, "changes": json.loads(row["changes"]) if row["changes"] else {}}) for row in rows]

@router.get("/audit/events/{user_id}", response_model=List[AuditEvent])
async def get_user_audit_events(user_id: str):
    connection = await connect_to_db()
    rows = await connection.fetch("SELECT * FROM audit_events WHERE user_id = $1", user_id)
    await close_db_connection(connection)
    
    return [AuditEvent(**{**row, "changes": json.loads(row["changes"]) if row["changes"] else {}}) for row in rows]