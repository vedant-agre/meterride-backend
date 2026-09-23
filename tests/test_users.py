import pytest
from fastapi.testclient import TestClient


def test_get_current_user_profile(client: TestClient, rider_data: dict):
    response = client.get("/users/me", headers=rider_data["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(rider_data["user"].id)
    assert data["name"] == rider_data["user"].name
    assert data["email"] == rider_data["user"].email
    assert data["phone"] == rider_data["user"].phone
    assert data["role"] == "RIDER"
    assert data["is_active"] is True
    assert "password_hash" not in data


def test_patch_user_profile(client: TestClient, rider_data: dict):
    update_payload = {
        "name": "Alice Updated",
        "phone": "+919999888877",
    }
    response = client.patch(
        "/users/me", json=update_payload, headers=rider_data["headers"]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alice Updated"
    assert data["phone"] == "+919999888877"
    assert "password_hash" not in data


def test_patch_user_duplicate_phone(
    client: TestClient, rider_data: dict, driver_data: dict
):
    # Try updating rider's phone to driver's phone
    conflict_payload = {
        "phone": driver_data["user"].phone,
    }
    response = client.patch(
        "/users/me", json=conflict_payload, headers=rider_data["headers"]
    )
    assert response.status_code == 409
    assert "Phone number is already in use" in response.json()["detail"]


def test_unauthorized_user_profile_access(client: TestClient):
    response = client.get("/users/me")
    assert response.status_code in (401, 403)

    response = client.patch("/users/me", json={"name": "Ghost"})
    assert response.status_code in (401, 403)
