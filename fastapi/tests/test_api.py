import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime
from app.models.audit_event import AuditEventAction

# Initialize the TestClient for the FastAPI application
client = TestClient(app)

def get_auth_headers():
    return {
        "Authorization": "Bearer test"
    }

def test_read_root():
    # Test the root endpoint to ensure it returns a welcome message
    response = client.get("/", headers=get_auth_headers())
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the User Audit API!"}

@pytest.mark.asyncio
async def test_create_user_profile(db_setup):
    # Test creating a new user profile
    profile_data = {
        "name": "John Doe",
        "email": "john.doe@example.com"
    }
    response = client.post("/api/v1/users/profile/", json=profile_data, headers=get_auth_headers())
    assert response.status_code == 201  # Check if the profile was created successfully
    assert response.json()["name"] == profile_data["name"]  # Verify the name
    assert response.json()["email"] == profile_data["email"]  # Verify the email
    assert "id" in response.json()  # Ensure an ID is returned
    assert response.json()["id"] is not None  # Ensure the ID is not None

@pytest.mark.asyncio
async def test_update_user_profile(db_setup):
    # Test updating an existing user profile
    # First, create a user profile
    profile_data = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data, headers=get_auth_headers())
    user_id = create_response.json()["id"]  # Store the user ID for later use
    
    # Update the user profile
    updated_data = {
        "name": "Jane Smith",
        "email": "jane.smith@example.com"
    }
    update_response = client.put(f"/api/v1/users/{user_id}/profile/", json=updated_data, headers=get_auth_headers())
    assert update_response.status_code == 200  # Check if the update was successful
    assert update_response.json()["name"] == updated_data["name"]  # Verify the updated name
    
    # Verify that the audit recorded the change
    audit_response = client.get(f"/api/v1/audit/events/{user_id}", headers=get_auth_headers())
    assert audit_response.status_code == 200
    events = audit_response.json()
    assert len(events) == 2  # Should have 2 events: creation and update
    assert events[-1]["action"] == AuditEventAction.UPDATE_PROFILE.value  # Check the action type
    assert "changes" in events[-1]  # Ensure changes are recorded

@pytest.mark.asyncio
async def test_get_user_profile(db_setup):
    # Test retrieving a user profile
    # First, create a user profile
    profile_data = {
        "name": "Test User",
        "email": "test@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data, headers=get_auth_headers())
    user_id = create_response.json()["id"]  # Store the user ID for retrieval
    
    # Retrieve the user profile
    get_response = client.get(f"/api/v1/users/{user_id}/profile/", headers=get_auth_headers())
    assert get_response.status_code == 200  # Check if the retrieval was successful
    assert get_response.json()["name"] == profile_data["name"]  # Verify the name matches

@pytest.mark.asyncio
async def test_create_audit_event(db_setup):
    # Test creating an audit event when a user profile is created
    # Create a user profile
    profile_data = {
        "name": "User for Audit",
        "email": "audit.user@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data, headers=get_auth_headers())
    user_id = create_response.json()["id"]  # Store the user ID

    # Verify that the profile was created successfully
    assert create_response.status_code == 201
    assert create_response.json()["name"] == profile_data["name"]

    # Check if the audit event was created for the profile creation
    audit_response = client.get(f"/api/v1/audit/events/{user_id}", headers=get_auth_headers())
    assert audit_response.status_code == 200
    events = audit_response.json()
    assert len(events) > 0  # Ensure at least one event exists
    assert events[-1]["action"] == AuditEventAction.CREATE_PROFILE.value  # Check the action type
    assert events[-1]["user_id"] == user_id  # Verify the user ID in the event
    assert events[-1]["details"] == f"User profile created."  # Check the event details

@pytest.mark.asyncio
async def test_get_audit_events(db_setup):
    # Test retrieving all audit events
    response = client.get("/api/v1/audit/events/", headers=get_auth_headers())
    assert response.status_code == 200  # Check if the retrieval was successful
    assert isinstance(response.json(), list)  # Ensure the response is a list
    assert len(response.json()) > 0  # Ensure there are events to return

@pytest.mark.asyncio
async def test_get_user_audit_events(db_setup):
    # Test retrieving audit events for a specific user
    # First, create a user profile
    profile_data = {
        "name": "User for Audit 2",
        "email": "audit.user2@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data, headers=get_auth_headers())
    user_id = create_response.json()["id"]  # Store the user ID

    # Verify if the profile was created successfully
    assert create_response.status_code == 201
    assert create_response.json()["name"] == profile_data["name"]

    # Update user data twice
    update_data_1 = {
        "name": "Updated User Name",
        "email": "updated.user2@example.com"
    }
    update_response_1 = client.put(f"/api/v1/users/{user_id}/profile", json=update_data_1, headers=get_auth_headers())
    assert update_response_1.status_code == 200  # Check if the first update was successful

    update_data_2 = {
        "name": "Another Update",
        "email": "another.update2@example.com"
    }
    update_response_2 = client.put(f"/api/v1/users/{user_id}/profile", json=update_data_2, headers=get_auth_headers())
    assert update_response_2.status_code == 200  # Check if the second update was successful

    # Fetch all audit events for the user
    response = client.get(f"/api/v1/audit/events/{user_id}", headers=get_auth_headers())
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)  # Ensure the response is a list
    assert len(events) > 0  # Ensure there are events to return

    # Verify that the audit events correspond to the updates
    assert any(event["action"] == AuditEventAction.UPDATE_PROFILE.value for event in events)  # Check for update actions
    assert any(event["user_id"] == user_id for event in events)  # Check for the correct user ID

@pytest.mark.asyncio
async def test_delete_user_profile(db_setup):
    # Test deleting a user profile
    # First, create a user profile
    profile_data = {
        "name": "John Field",
        "email": "john.field@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data, headers=get_auth_headers())
    user_id = create_response.json()["id"]  # Store the user ID
    
    # Delete the user profile
    delete_response = client.delete(f"/api/v1/users/{user_id}/profile/", headers=get_auth_headers())
    assert delete_response.status_code == 204  # Check if the deletion was successful
    
    # Verify that the profile is marked as deleted
    get_response = client.get(f"/api/v1/users/{user_id}/profile/", headers=get_auth_headers())
    assert get_response.status_code == 404  # The profile should not be found

    # Check if the audit event was created
    audit_response = client.get(f"/api/v1/audit/events/{user_id}", headers=get_auth_headers())
    assert audit_response.status_code == 200
    events = audit_response.json()
    assert len(events) > 0  # Ensure there are events to return
    assert events[-1]["action"] == AuditEventAction.DELETE_PROFILE.value  # Check the action type
    assert events[-1]["details"] == f"User profile deleted."  # Check the event details

@pytest.mark.asyncio
async def test_get_active_user_profiles(db_setup):
    # Test retrieving active user profiles
    # First, create a user profile
    profile_data = {
        "name": "Active User",
        "email": "active.user@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data, headers=get_auth_headers())
    user_id = create_response.json()["id"]  # Store the user ID

    # Delete the profile
    delete_response = client.delete(f"/api/v1/users/{user_id}/profile/", headers=get_auth_headers())
    assert delete_response.status_code == 204  # Check if the deletion was successful

    # Obtain active profiles
    active_response = client.get("/api/v1/users/profiles/active/", headers=get_auth_headers())
    assert active_response.status_code == 200  # Check if the retrieval was successful
    active_profiles = active_response.json()
    assert len(active_profiles) == 5  # Should return only non-deleted profiles

@pytest.mark.asyncio
async def test_get_all_user_profiles(db_setup):
    # Test retrieving all user profiles
    all_response = client.get("/api/v1/users/profile/", headers=get_auth_headers())
    assert all_response.status_code == 200  # Check if the retrieval was successful
    all_profiles = all_response.json()
    assert isinstance(all_profiles, list)  # Ensure the response is a list

@pytest.mark.asyncio
async def test_get_deleted_user_profile(db_setup):
    # Test retrieving a deleted user profile
    # First, create a user profile
    profile_data = {
        "name": "Deleted User",
        "email": "deleted.user@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data, headers=get_auth_headers())
    user_id = create_response.json()["id"]  # Store the user ID

    # Delete the profile
    client.delete(f"/api/v1/users/{user_id}/profile/", headers=get_auth_headers())

    # Attempt to retrieve the deleted profile
    deleted_response = client.get(f"/api/v1/users/{user_id}/profile/", headers=get_auth_headers())
    assert deleted_response.status_code == 404  # The profile should not be found
    assert deleted_response.json() == {"detail": "User deleted"}  # Check the response detail

@pytest.mark.asyncio
async def test_restore_deleted_user_profile(db_setup):
    # Test restoring a deleted user profile
    # First, create a user profile
    profile_data = {
        "name": "User to Restore",
        "email": "restore.user@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data, headers=get_auth_headers())
    user_id = create_response.json()["id"]  # Store the user ID

    # Delete the profile
    delete_response = client.delete(f"/api/v1/users/{user_id}/profile/", headers=get_auth_headers())
    assert delete_response.status_code == 204  # Check if the deletion was successful

    # Verify if the profile was marked as deleted
    get_response = client.get(f"/api/v1/users/{user_id}/profile/", headers=get_auth_headers())
    assert get_response.status_code == 404  # The profile should not be found

    # Restore the profile
    restore_response = client.post(f"/api/v1/users/{user_id}/profile/restore/", headers=get_auth_headers())  # Verify if the endpoint is correct
    assert restore_response.status_code == 200  # Check if the restoration was successful
    assert restore_response.json()["is_deleted"] is False  # Ensure the profile is no longer deleted

    # Verify if the profile was restored
    restored_profile = client.get(f"/api/v1/users/{user_id}/profile/", headers=get_auth_headers())
    assert restored_profile.status_code == 200  # Check if the retrieval was successful
    assert restored_profile.json()["name"] == profile_data["name"]  # Verify the name matches

@pytest.mark.asyncio
async def test_change_and_rollback_user_profile(db_setup):
    # Test changing a user profile and rolling back the changes
    # Create a user profile
    profile_data = {
        "name": "User to Change And Rollback",
        "email": "change.user.rollback@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data, headers=get_auth_headers())
    user_id = create_response.json()["id"]  # Store the user ID

    # Update the user profile
    updated_data = {
        "name": "Changed User",
        "email": "changed.user.rollback@example.com"
    }
    update_response = client.put(f"/api/v1/users/{user_id}/profile/", json=updated_data, headers=get_auth_headers())
    assert update_response.status_code == 200  # Check if the update was successful

    # Verify if the changes were applied
    updated_profile = client.get(f"/api/v1/users/{user_id}/profile/", headers=get_auth_headers())
    assert updated_profile.json()["name"] == updated_data["name"]  # Verify the updated name

    # Retrieve the audit event for the user
    audit_event = client.get(f"/api/v1/audit/events/{user_id}", headers=get_auth_headers())
    assert audit_event.status_code == 200
    
    # Ensure the response is a list and get the first event
    events = audit_event.json()
    assert isinstance(events, list)
    assert len(events) > 0
    audit_event_id = events[1]["id"]  # Get the ID of the audit event

    # Rollback the changes using the correct endpoint
    rollback_response = client.post(f"/api/v1/audit/events/rollback/{audit_event_id}", headers=get_auth_headers())  # Use a valid audit event ID
    assert rollback_response.status_code == 200  # Check if the rollback was successful

    # Verify if the changes were reverted
    rolled_back_profile = client.get(f"/api/v1/users/{user_id}/profile/", headers=get_auth_headers())
    assert rolled_back_profile.json()["name"] == profile_data["name"]  # Verify the name matches the original
    assert rolled_back_profile.json()["email"] == profile_data["email"]  # Verify the email matches the original

@pytest.mark.asyncio
async def test_audit_event_creation_on_delete(db_setup):
    # Test that an audit event is created when a user profile is deleted
    # First, create a user profile
    profile_data = {
        "name": "User for Audit Creation",
        "email": "audit.user.creation@example.com"
    }
    create_response = client.post("/api/v1/users/profile/", json=profile_data, headers=get_auth_headers())
    user_id = create_response.json()["id"]  # Store the user ID

    # Delete the profile
    delete_response = client.delete(f"/api/v1/users/{user_id}/profile/", headers=get_auth_headers())
    assert delete_response.status_code == 204  # Check if the deletion was successful

    # Verify if the audit event was created
    audit_response = client.get(f"/api/v1/audit/events/{user_id}", headers=get_auth_headers())
    assert audit_response.status_code == 200
    events = audit_response.json()
    assert len(events) > 0  # Ensure there are events to return
    assert events[-1]["action"] == AuditEventAction.DELETE_PROFILE.value  # Check the action type
    assert events[-1]["details"] == f"User profile deleted."  # Check the event details
