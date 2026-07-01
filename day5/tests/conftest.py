"""Pytest configuration and shared fixtures."""

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("API_KEY", "test-api-key")

import api.main as main_app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_servers():
    """Isolate in-memory server store between tests."""
    main_app._servers.clear()
    main_app._next_id = 1
    yield
    main_app._servers.clear()
    main_app._next_id = 1


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(main_app.app)


@pytest.fixture
def api_headers() -> dict[str, str]:
    """Valid API key headers."""
    return {"X-API-Key": "test-api-key"}
