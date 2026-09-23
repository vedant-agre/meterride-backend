import pytest
from fastapi.testclient import TestClient


def test_driver_registration(client: TestClient):
    # 1. Register a new rider
    reg_payload = {
        "name": "Newbie Driver",
        "email": "newbie.driver@example.com",
        "phone": "+919876540055",
        "password": "Password123!",
        "role": "RIDER",
    }
    resp = client.post("/auth/register", json=reg_payload)
    assert resp.status_code == 201

    # Login to get token
    login_resp = client.post(
        "/auth/login",
        json={"email": reg_payload["email"], "password": reg_payload["password"]},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register as driver
    driver_payload = {"license_number": "DL-MH-12-20249999"}
    reg_driver_resp = client.post(
        "/drivers/register", json=driver_payload, headers=headers
    )
    assert reg_driver_resp.status_code == 201
    driver_data = reg_driver_resp.json()
    assert driver_data["license_number"] == "DL-MH-12-20249999"
    assert driver_data["status"] == "OFFLINE"
    assert float(driver_data["rating_average"]) == 5.0
    assert driver_data["total_rides"] == 0
    assert driver_data["current_latitude"] is None
    assert driver_data["current_longitude"] is None

    # Verify user's role is now elevated to DRIVER
    me_resp = client.get("/users/me", headers=headers)
    assert me_resp.json()["role"] == "DRIVER"

    # 3. Duplicate driver registration by same user fails
    dup_driver_resp = client.post(
        "/drivers/register",
        json={"license_number": "DL-MH-12-DIFFERENT"},
        headers=headers,
    )
    assert dup_driver_resp.status_code == 409
    assert "User already has a registered driver profile" in dup_driver_resp.json()["detail"]


def test_duplicate_license_number_registration(client: TestClient, driver_data: dict):
    # Register another user
    reg_payload = {
        "name": "Another Driver",
        "email": "another.driver@example.com",
        "phone": "+919876540056",
        "password": "Password123!",
        "role": "RIDER",
    }
    client.post("/auth/register", json=reg_payload)
    login_resp = client.post(
        "/auth/login",
        json={"email": reg_payload["email"], "password": reg_payload["password"]},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # Try registering with driver_data's existing license number
    conflict_payload = {"license_number": driver_data["driver"].license_number}
    resp = client.post("/drivers/register", json=conflict_payload, headers=headers)
    assert resp.status_code == 409
    assert "Driver license number is already registered" in resp.json()["detail"]


def test_get_driver_profile(client: TestClient, driver_data: dict):
    resp = client.get("/drivers/me", headers=driver_data["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(driver_data["driver"].id)
    assert data["user_id"] == str(driver_data["user"].id)
    assert data["license_number"] == driver_data["driver"].license_number
    assert data["status"] == "OFFLINE"


def test_patch_driver_profile(
    client: TestClient, driver_data: dict, second_driver_data: dict
):
    # Success update
    update_payload = {"license_number": "DL-MH-12-UPDATED123"}
    resp = client.patch(
        "/drivers/me", json=update_payload, headers=driver_data["headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["license_number"] == "DL-MH-12-UPDATED123"

    # Conflict with second driver's license
    conflict_payload = {"license_number": second_driver_data["driver"].license_number}
    resp = client.patch(
        "/drivers/me", json=conflict_payload, headers=driver_data["headers"]
    )
    assert resp.status_code == 409
    assert "License number is already registered" in resp.json()["detail"]


def test_driver_status_update(client: TestClient, driver_data: dict):
    # 1. Attempting to set AVAILABLE without an active vehicle fails with 400
    status_payload = {"status": "AVAILABLE"}
    resp = client.patch(
        "/drivers/status", json=status_payload, headers=driver_data["headers"]
    )
    assert resp.status_code == 400
    assert "Cannot set status to AVAILABLE without an active vehicle" in resp.json()["detail"]

    # 2. Add an active vehicle for the driver
    vehicle_payload = {
        "vehicle_type": "SEDAN",
        "registration_number": "MH12XY9999",
        "model": "Honda City",
        "color": "Silver",
        "capacity": 4,
    }
    veh_resp = client.post(
        "/vehicles", json=vehicle_payload, headers=driver_data["headers"]
    )
    assert veh_resp.status_code == 201

    # 3. Now setting AVAILABLE succeeds
    resp = client.patch(
        "/drivers/status", json=status_payload, headers=driver_data["headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "AVAILABLE"
    assert resp.json()["driver_id"] == str(driver_data["driver"].id)

    # 4. Set to BUSY
    busy_resp = client.patch(
        "/drivers/status", json={"status": "BUSY"}, headers=driver_data["headers"]
    )
    assert busy_resp.status_code == 200
    assert busy_resp.json()["status"] == "BUSY"


def test_rider_cannot_access_driver_me(client: TestClient, rider_data: dict):
    resp = client.get("/drivers/me", headers=rider_data["headers"])
    assert resp.status_code == 403
