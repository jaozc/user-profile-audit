from fastapi import APIRouter, HTTPException
from app.models.audit_event import AuditEvent
from app.models.user_profile import UserProfile, UserProfileCreate
from typing import List
from datetime import datetime
import uuid

router = APIRouter()

# Simulando bancos de dados em memória
audit_events_db = []
user_profiles_db = {}

@router.post("/users/profile/", response_model=UserProfile)
async def create_user_profile(profile: UserProfileCreate):
    user_id = str(uuid.uuid4())
    new_profile = UserProfile(
        id=user_id,
        name=profile.name,
        email=profile.email
    )
    
    user_profiles_db[user_id] = new_profile
    
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
    audit_events_db.append(audit_event)
    
    return new_profile

@router.put("/users/{user_id}/profile/", response_model=UserProfile)
async def update_user_profile(user_id: str, profile: UserProfileCreate):
    if user_id not in user_profiles_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    old_profile = user_profiles_db[user_id]
    changes = {}
    
    # Detecta mudanças nos campos
    if old_profile.name != profile.name:
        changes["name"] = {"old": old_profile.name, "new": profile.name}
    if old_profile.email != profile.email:
        changes["email"] = {"old": old_profile.email, "new": profile.email}
    
    # Atualiza o perfil
    updated_profile = UserProfile(
        id=user_id,
        name=profile.name,
        email=profile.email
    )
    user_profiles_db[user_id] = updated_profile
    
    # Registra evento de auditoria para atualização
    if changes:
        audit_event = AuditEvent(
            user_id=user_id,
            action="UPDATE_PROFILE",
            resource="user_profile",
            details="Perfil atualizado",
            changes=changes
        )
        audit_events_db.append(audit_event)
    
    return updated_profile

@router.get("/users/{user_id}/profile/", response_model=UserProfile)
async def get_user_profile(user_id: str):
    if user_id not in user_profiles_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user_profiles_db[user_id]

# Mantém os endpoints existentes de auditoria
@router.post("/audit/events/", response_model=AuditEvent)
async def create_audit_event(event: AuditEvent):
    audit_events_db.append(event)
    return event

@router.get("/audit/events/", response_model=List[AuditEvent])
async def get_audit_events():
    return audit_events_db

@router.get("/audit/events/{user_id}", response_model=List[AuditEvent])
async def get_user_audit_events(user_id: str):
    events = [event for event in audit_events_db if event.user_id == user_id]
    return events