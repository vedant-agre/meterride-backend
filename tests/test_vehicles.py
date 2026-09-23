import uuid
import pytest
from fastapi.testclient import TestClient


def test_vehicle_creation_and_retrieval(client: TestClient, driver_data: dict):
    # 1. Create a vehicle
    vehicle_payload = {
        "vehicle_type": "SEDAN",
        "registration_number": "MH12AB1111",
        "model": "Hyundai Verna",
        "color": "White",
        "capacity": 4,
    }
    create_resp = client.post(
        "/vehicles", json=vehicle_payload, headers=driver_data["headers"]
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["registration_number"] == "MH12AB1111"
    assert created["driver_id"] == str(driver_data["driver"].id)
    assert created["is_active"] is True
    assert "id" in created
    vehicle_id = created["id"]

    # 2. List vehicles
    list_resp = client.get("/vehicles", headers=driver_data["headers"])
    assert list_resp.status_code == 200
    vehicles = list_resp.json()
    assert len(vehicles) >= 1
    assert any(v["id"] == vehicle_id for v in vehicles)

    # 3. Get single vehicle by ID
    get_resp = client.get(f"/vehicles/{vehicle_id}", headers=driver_data["headers"])
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == vehicle_id


def test_vehicle_creation_duplicate_registration(
    client: TestClient, driver_data: dict, second_driver_data: dict
):
    payload = {
        "vehicle_type": "AUTO",
        "registration_number": "MH12AUTO01",
        "model": "Bajaj Compact",
        "color": "Yellow-Black",
        "capacity": 3,
    }
    first_resp = client.post("/vehicles", json=payload, headers=driver_data["headers"])
    assert first_resp.status_code == 201

    # Second driver tries with same registration number
    dup_resp = client.post(
        "/vehicles", json=payload, headers=second_driver_data["headers"]
    )
    assert dup_resp.status_code == 409
    assert "Vehicle registration number is already registered" in dup_resp.json()["detail"]


def test_vehicle_validation_errors(client: TestClient, driver_data: dict):
    # Invalid capacity (< 1)
    invalid_capacity = {
        "vehicle_type": "SEDAN",
        "registration_number": "MH12BADCAP",
        "model": "Car",
        "color": "Blue",
        "capacity": 0,
    }
    resp = client.post("/vehicles", json=invalid_capacity, headers=driver_data["headers"])
    assert resp.status_code == 422

    # Invalid vehicle type
    invalid_type = {
        "vehicle_type": "AIRPLANE",
        "registration_number": "MH12BADTYPE",
        "model": "Jet",
        "color": "White",
        "capacity": 2,
    }
    resp = client.post("/vehicles", json=invalid_type, headers=driver_data["headers"])
    assert resp.status_code == 422


def test_vehicle_update(client: TestClient, driver_data: dict):
    payload = {
        "vehicle_type": "SUV",
        "registration_number": "MH12SUV001",
        "model": "Mahindra XUV700",
        "color": "Midnight Black",
        "capacity": 7,
    }
    create_resp = client.post("/vehicles", json=payload, headers=driver_data["headers"])
    vehicle_id = create_resp.json()["id"]

    update_payload = {"color": "Silver", "model": "Mahindra XUV700 AX7"}
    update_resp = client.patch(
        f"/vehicles/{vehicle_id}", json=update_payload, headers=driver_data["headers"]
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["color"] == "Silver"
    assert data["model"] == "Mahindra XUV700 AX7"


def test_vehicle_deletion_and_deactivation(client: TestClient, driver_data: dict):
    payload = {
        "vehicle_type": "BIKE",
        "registration_number": "MH12BIKE01",
        "model": "Royal Enfield Classic 350",
        "color": "Black",
        "capacity": 1,
    }
    create_resp = client.post("/vehicles", json=payload, headers=driver_data["headers"])
    vehicle_id = create_resp.json()["id"]

    # Delete vehicle (soft delete)
    del_resp = client.delete(f"/vehicles/{vehicle_id}", headers=driver_data["headers"])
    assert del_resp.status_code == 204

    # Verify vehicle status is deactivated
    get_resp = client.get(f"/vehicles/{vehicle_id}", headers=driver_data["headers"])
    assert get_resp.status_code == 200
    assert get_resp.json()["is_active"] is False


def test_vehicle_ownership_restrictions(
    client: TestClient, driver_data: dict, second_driver_data: dict, admin_data: dict
):
    # Driver 1 registers a vehicle
    payload = {
        "vehicle_type": "SEDAN",
        "registration_number": "MH12OWNER01",
        "model": "Honda Amaze",
        "color": "Red",
        "capacity": 4,
    }
    resp = client.post("/vehicles", json=payload, headers=driver_data["headers"])
    vehicle_id = resp.json()["id"]

    # Driver 2 tries to GET driver 1's vehicle -> 403 Forbidden
    get_resp = client.get(
        f"/vehicles/{vehicle_id}", headers=second_driver_data["headers"]
    )
    assert get_resp.status_code == 403
    assert "Driver does not own this vehicle" in get_resp.json()["detail"]

    # Driver 2 tries to PATCH driver 1's vehicle -> 403 Forbidden
    patch_resp = client.patch(
        f"/vehicles/{vehicle_id}",
        json={"color": "Green"},
        headers=second_driver_data["headers"],
    )
    assert patch_resp.status_code == 403
    assert "Driver does not own this vehicle" in patch_resp.json()["detail"]

    # Driver 2 tries to DELETE driver 1's vehicle -> 403 Forbidden
    del_resp = client.delete(
        f"/vehicles/{vehicle_id}", headers=second_driver_data["headers"]
    )
    assert del_resp.status_code == 403
    assert "Driver does not own this vehicle" in del_resp.json()["detail"]

    # Admin CAN view driver 1's vehicle -> 200 OK
    admin_resp = client.get(f"/vehicles/{vehicle_id}", headers=admin_data["headers"])
    assert admin_resp.status_code == 200
    assert admin_resp.json()["id"] == vehicle_id


def test_rider_cannot_manage_vehicles(client: TestClient, rider_data: dict):
    payload = {
        "vehicle_type": "SEDAN",
        "registration_number": "MH12RIDER01",
        "model": "Swift",
        "color": "White",
        "capacity": 4,
    }
    resp = client.post("/vehicles", json=payload, headers=rider_data["headers"])
    assert resp.status_code == 403

    resp = client.get("/vehicles", headers=rider_data["headers"])
    assert resp.status_code == 403


def test_vehicle_not_found(client: TestClient, driver_data: dict):
    fake_id = uuid.uuid4()
    resp = client.get(f"/vehicles/{fake_id}", headers=driver_data["headers"])
    assert resp.status_code == 404

    resp = client.patch(
        f"/vehicles/{fake_id}", json={"color": "Pink"}, headers=driver_data["headers"]
    )
    assert resp.status_code == 404

    resp = client.delete(f"/vehicles/{fake_id}", headers=driver_data["headers"])
    assert resp.status_code == 404
