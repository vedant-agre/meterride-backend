import pytest
from fastapi.testclient import TestClient

from app.core.security import decode_access_token


def test_successful_registration(client: TestClient):
    payload = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "phone": "+919876543210",
        "password": "SecurePassword123!",
        "role": "RIDER",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert data["phone"] == payload["phone"]
    assert data["role"] == "RIDER"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "password_hash" not in data


def test_duplicate_email_registration(client: TestClient):
    payload = {
        "name": "User One",
        "email": "duplicate@example.com",
        "phone": "+919876540001",
        "password": "Password123!",
        "role": "RIDER",
    }
    first_resp = client.post("/auth/register", json=payload)
    assert first_resp.status_code == 201

    payload_duplicate_email = {
        "name": "User Two",
        "email": "duplicate@example.com",
        "phone": "+919876540002",
        "password": "Password123!",
        "role": "RIDER",
    }
    second_resp = client.post("/auth/register", json=payload_duplicate_email)
    assert second_resp.status_code == 409
    assert "Email is already registered" in second_resp.json()["detail"]


def test_duplicate_phone_registration(client: TestClient):
    payload = {
        "name": "Phone User One",
        "email": "phone1@example.com",
        "phone": "+919876540099",
        "password": "Password123!",
        "role": "RIDER",
    }
    first_resp = client.post("/auth/register", json=payload)
    assert first_resp.status_code == 201

    payload_duplicate_phone = {
        "name": "Phone User Two",
        "email": "phone2@example.com",
        "phone": "+919876540099",
        "password": "Password123!",
        "role": "RIDER",
    }
    second_resp = client.post("/auth/register", json=payload_duplicate_phone)
    assert second_resp.status_code == 409
    assert "Phone number is already registered" in second_resp.json()["detail"]


def test_registration_validation_errors(client: TestClient):
    # Password too short (<8 chars)
    short_pw = {
        "name": "Short PW",
        "email": "shortpw@example.com",
        "phone": "+919876540011",
        "password": "short",
        "role": "RIDER",
    }
    resp = client.post("/auth/register", json=short_pw)
    assert resp.status_code == 422

    # Invalid email format
    invalid_email = {
        "name": "Bad Email",
        "email": "not-an-email",
        "phone": "+919876540012",
        "password": "ValidPassword123!",
        "role": "RIDER",
    }
    resp = client.post("/auth/register", json=invalid_email)
    assert resp.status_code == 422


def test_successful_login(client: TestClient):
    # Register first
    reg_payload = {
        "name": "Login User",
        "email": "loginuser@example.com",
        "phone": "+919876540020",
        "password": "LoginSecret123!",
        "role": "RIDER",
    }
    reg_resp = client.post("/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201

    # Login
    login_payload = {
        "email": "loginuser@example.com",
        "password": "LoginSecret123!",
    }
    login_resp = client.post("/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["user"]["email"] == "loginuser@example.com"
    assert token_data["user"]["name"] == "Login User"
    assert "password_hash" not in token_data["user"]

    # Verify decoded JWT
    decoded = decode_access_token(token_data["access_token"])
    assert decoded["email"] == "loginuser@example.com"
    assert "sub" in decoded


def test_login_invalid_password(client: TestClient):
    reg_payload = {
        "name": "Wrong Password User",
        "email": "wrongpw@example.com",
        "phone": "+919876540021",
        "password": "CorrectPassword123!",
    }
    client.post("/auth/register", json=reg_payload)

    login_payload = {
        "email": "wrongpw@example.com",
        "password": "IncorrectPassword999!",
    }
    resp = client.post("/auth/login", json=login_payload)
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    login_payload = {
        "email": "nonexistent@example.com",
        "password": "SomePassword123!",
    }
    resp = client.post("/auth/login", json=login_payload)
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]


def test_jwt_authentication_flow(client: TestClient, rider_data: dict):
    # Valid token works
    response = client.get("/users/me", headers=rider_data["headers"])
    assert response.status_code == 200
    assert response.json()["email"] == rider_data["user"].email

    # Invalid token fails
    bad_headers = {"Authorization": "Bearer invalid.token.payload"}
    response = client.get("/users/me", headers=bad_headers)
    assert response.status_code == 401

    # Missing token fails
    response = client.get("/users/me")
    assert response.status_code in (401, 403)
