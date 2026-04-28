"""
conftest.py — shared fixtures for all tests.
"""
import os
import pytest
from dotenv import load_dotenv
from faker import Faker
from utils.auth import get_token, auth_headers

load_dotenv()

fake = Faker()


@pytest.fixture(scope="session")
def base_url():
    return os.getenv("BASE_URL", "https://api.zedu.chat/api/v1")


@pytest.fixture(scope="session")
def token():
    """Session-scoped token — login once, reuse across all tests."""
    return get_token()


@pytest.fixture(scope="session")
def headers(token):
    """Session-scoped auth headers."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def unique_email():
    """Fresh unique email for each test that needs registration."""
    return f"qa_{fake.uuid4()[:8]}@mailtest.dev"


@pytest.fixture
def unique_user():
    """Full unique user payload."""
    return {
        "email": f"qa_{fake.uuid4()[:8]}@mailtest.dev",
        "password": "Test@1234!",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "username": fake.user_name() + fake.uuid4()[:5],
    }
