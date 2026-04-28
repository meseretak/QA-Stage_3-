"""
Shared authentication utility.
All tests that need a token call get_token() from here.
No tokens are hardcoded anywhere in the codebase.
"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://api.zedu.chat/api/v1")
TEST_EMAIL = os.getenv("TEST_EMAIL")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")


def get_token(email: str = None, password: str = None) -> str:
    """Login and return a bearer token. Raises on failure."""
    email = email or TEST_EMAIL
    password = password or TEST_PASSWORD
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    token = (
        data.get("data", {}).get("token")
        or data.get("token")
        or data.get("access_token")
        or data.get("data", {}).get("access_token")
    )
    if not token:
        raise ValueError(f"Token not found in login response: {data}")
    return token


def auth_headers(email: str = None, password: str = None) -> dict:
    """Return Authorization header dict ready to pass to requests."""
    return {"Authorization": f"Bearer {get_token(email, password)}"}
