"""Integration tests against a running Docker Compose stack."""

import json
import os
import time

import httpx
import pytest
import websockets

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:8501")
API_KEY = os.getenv("API_KEY") or "dev-key-change-me"
WS_URL = (
    API_BASE_URL.replace("http://", "ws://").replace("https://", "wss://")
    + "/ws/metrics"
)


def _wait_for_service(url: str, timeout: float = 60.0) -> None:
    """Block until an HTTP endpoint responds with 200."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=2.0, follow_redirects=True)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(1)
    pytest.fail(f"Service not ready at {url}")


@pytest.fixture(scope="module", autouse=True)
def wait_for_stack():
    """Ensure the stack is up before integration tests run."""
    _wait_for_service(f"{API_BASE_URL}/health")
    _wait_for_service(DASHBOARD_URL)


def test_integration_health():
    response = httpx.get(f"{API_BASE_URL}/health", timeout=5.0)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_integration_metrics():
    response = httpx.get(f"{API_BASE_URL}/metrics", timeout=5.0)
    assert response.status_code == 200
    body = response.json()
    for field in ("cpu_percent", "memory_percent", "disk_percent"):
        assert field in body
        assert 0 <= body[field] <= 100


def test_integration_servers_crud():
    headers = {"X-API-Key": API_KEY}
    denied = httpx.post(
        f"{API_BASE_URL}/servers",
        json={"name": "no-key", "host": "api", "port": 8000},
        timeout=5.0,
    )
    assert denied.status_code == 403

    created = httpx.post(
        f"{API_BASE_URL}/servers",
        json={"name": "integration-api", "host": "api", "port": 8000},
        headers=headers,
        timeout=5.0,
    )
    assert created.status_code == 201
    server_id = created.json()["id"]

    listed = httpx.get(f"{API_BASE_URL}/servers", timeout=5.0)
    assert listed.status_code == 200
    assert any(s["id"] == server_id for s in listed.json())

    checked = httpx.post(
        f"{API_BASE_URL}/servers/{server_id}/check",
        headers=headers,
        timeout=5.0,
    )
    assert checked.status_code == 200
    assert checked.json()["status"] in ("UP", "DEGRADED", "DOWN", "UNKNOWN")

    deleted = httpx.delete(
        f"{API_BASE_URL}/servers/{server_id}",
        headers=headers,
        timeout=5.0,
    )
    assert deleted.status_code == 204


def test_integration_dashboard_reachable():
    response = httpx.get(DASHBOARD_URL, timeout=5.0, follow_redirects=True)
    assert response.status_code == 200
    body = response.text.lower()
    assert "streamlit" in body or "devops" in body


@pytest.mark.asyncio
async def test_integration_websocket():
    async with websockets.connect(WS_URL) as websocket:
        raw = await websocket.recv()
        frame = json.loads(raw)
        assert "cpu_percent" in frame
        assert "memory_percent" in frame

        start = time.monotonic()
        await websocket.recv()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.9
