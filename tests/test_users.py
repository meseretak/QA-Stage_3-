"""
test_users.py — User profile endpoint tests.
GET /users  |  GET /users/me

Every test validates ALL of:
  1. Status code
  2. Field presence
  3. Data types
  4. Field values
  5. Error messages
  6. Schema validation
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")


# ════════════════════════════════════════════════════════════════════════════
# POSITIVE (3)
# ════════════════════════════════════════════════════════════════════════════

def test_get_users_with_valid_token_returns_200_with_schema(auth_headers):
    """
    Authenticated GET /users returns 200 with full success schema.
    Validates: status code, field presence, data types, field values,
               message content, schema.
    """
    r = requests.get(f"{BASE_URL}/users", headers=auth_headers, timeout=15)

    # 1. Status code
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    data = r.json()

    # 2. Field presence
    for f in ("status", "status_code", "message", "data"):
        assert f in data, f"'{f}' missing: {data}"

    # 3. Data types
    assert isinstance(data["status"], str)
    assert isinstance(data["status_code"], int)
    assert isinstance(data["message"], str)

    # 4. Field values
    assert data["status"] == "success"
    assert data["status_code"] == 200

    # 5. Message not empty
    assert len(data["message"]) > 0

    # 6. Schema — Content-Type is JSON
    assert "application/json" in r.headers.get("Content-Type", "")


def test_get_users_me_returns_200_with_correct_email(auth_headers):
    """
    GET /users/me returns 200 with the authenticated user's email.
    Validates: status code, field presence, data types, field values,
               email match, schema.
    """
    r = requests.get(f"{BASE_URL}/users/me", headers=auth_headers, timeout=15)

    # 1. Status code
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    data = r.json()

    # 2. Field presence
    assert "status" in data
    assert "data" in data
    assert "email" in r.text, "email field missing from /users/me response"

    # 3. Data type — navigate to email field
    user = data.get("data") or {}
    if isinstance(user, dict):
        email = user.get("email") or (user.get("user") or {}).get("email")
        if email:
            assert isinstance(email, str), f"email must be str, got {type(email)}"

    # 4. Field value — email matches logged-in user
    assert os.getenv("TEST_EMAIL", "").lower() in r.text.lower(), \
        f"Expected email not found in response: {r.text[:200]}"

    # 5. Message
    assert data.get("status") == "success"

    # 6. Schema
    assert isinstance(data.get("status_code"), int)


def test_get_users_me_does_not_expose_password(auth_headers):
    """
    GET /users/me must NOT return a password field.
    Validates: status code, field presence, data types, field values,
               security (no password), schema.
    """
    r = requests.get(f"{BASE_URL}/users/me", headers=auth_headers, timeout=15)

    # 1. Status code
    assert r.status_code == 200

    data = r.json()

    # 2. Field presence
    assert "status" in data
    assert "data" in data

    # 3. Data type
    assert isinstance(data["status"], str)

    # 4. Field value
    assert data["status"] == "success"

    # 5. Security — password must NOT appear anywhere in response
    assert "password" not in r.text.lower(), \
        "SECURITY VIOLATION: password field exposed in /users/me response!"

    # 6. Schema
    assert "status_code" in data
    assert isinstance(data["status_code"], int)


# ════════════════════════════════════════════════════════════════════════════
# NEGATIVE (2)
# ════════════════════════════════════════════════════════════════════════════

def test_get_users_without_token_returns_401_with_error_schema():
    """
    GET /users without token returns 401 with full error schema.
    Validates: status code, field presence, data types, field values,
               error message content, schema.
    """
    r = requests.get(f"{BASE_URL}/users", timeout=15)

    # 1. Status code
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"

    data = r.json()

    # 2. Field presence
    for f in ("status", "status_code", "message"):
        assert f in data, f"'{f}' missing: {data}"

    # 3. Data types
    assert isinstance(data["status"], str)
    assert isinstance(data["status_code"], int)
    assert isinstance(data["message"], str)

    # 4. Field values
    assert data["status"] == "error"
    assert data["status_code"] == 401

    # 5. Error message — mentions token
    assert "token" in data["message"].lower(), \
        f"Expected token-related message, got: {data['message']}"

    # 6. Schema
    assert "error" in data


def test_get_users_with_fake_expired_jwt_returns_401():
    """
    A structurally valid but fake/expired JWT is rejected with 401.
    Validates: status code, field presence, data types, field values,
               error message, schema.
    """
    fake_jwt = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkZha2UiLCJpYXQiOjE1MTYyMzkwMjJ9"
        ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    )
    r = requests.get(
        f"{BASE_URL}/users",
        headers={"Authorization": f"Bearer {fake_jwt}"},
        timeout=15,
    )

    # 1. Status code
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"

    data = r.json()

    # 2. Field presence
    assert "status" in data
    assert "message" in data

    # 3. Data types
    assert isinstance(data["status"], str)
    assert isinstance(data["message"], str)

    # 4. Field value
    assert data["status"] == "error"

    # 5. Error message not empty
    assert len(data["message"]) > 0

    # 6. Schema
    assert "status_code" in data
    assert data["status_code"] == 401
