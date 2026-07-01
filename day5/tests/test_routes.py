"""Unit tests for API routes."""

import json
import time

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_returns_fields(client: TestClient):
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.json()
    assert "cpu_percent" in body
    assert "memory_percent" in body
    assert "disk_percent" in body


def test_create_server_without_api_key_returns_403(client: TestClient):
    response = client.post(
        "/servers",
        json={"name": "api-prod", "host": "10.0.0.1", "port": 8080},
    )
    assert response.status_code == 403


def test_create_server_with_api_key_returns_201(client: TestClient, api_headers: dict):
    response = client.post(
        "/servers",
        json={"name": "api-prod", "host": "10.0.0.1", "port": 8080},
        headers=api_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "api-prod"
    assert body["host"] == "10.0.0.1"
    assert body["port"] == 8080
    assert "id" in body
    assert "status" in body


def test_list_servers_returns_registered(client: TestClient, api_headers: dict):
    client.post(
        "/servers",
        json={"name": "db", "host": "10.0.0.5", "port": 5432},
        headers=api_headers,
    )
    response = client.get("/servers")
    assert response.status_code == 200
    servers = response.json()
    assert len(servers) == 1
    assert servers[0]["name"] == "db"
    assert "status" in servers[0]


def test_delete_unknown_server_returns_404(client: TestClient, api_headers: dict):
    response = client.delete("/servers/999", headers=api_headers)
    assert response.status_code == 404


def test_delete_server_success(client: TestClient, api_headers: dict):
    create = client.post(
        "/servers",
        json={"name": "tmp", "host": "127.0.0.1", "port": 9000},
        headers=api_headers,
    )
    server_id = create.json()["id"]
    response = client.delete(f"/servers/{server_id}", headers=api_headers)
    assert response.status_code == 204
    assert client.get("/servers").json() == []


def test_manual_check_unknown_server_returns_404(client: TestClient, api_headers: dict):
    response = client.post("/servers/42/check", headers=api_headers)
    assert response.status_code == 404


def test_manual_check_returns_server(client: TestClient, api_headers: dict):
    create = client.post(
        "/servers",
        json={"name": "svc", "host": "10.0.0.9", "port": 9999},
        headers=api_headers,
    )
    server_id = create.json()["id"]
    response = client.post(f"/servers/{server_id}/check", headers=api_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == server_id
    assert body["status"] in ("UP", "DEGRADED", "DOWN", "UNKNOWN")


def test_create_server_invalid_port_returns_422(client: TestClient, api_headers: dict):
    response = client.post(
        "/servers",
        json={"name": "bad", "host": "10.0.0.1", "port": 0},
        headers=api_headers,
    )
    assert response.status_code == 422


def test_websocket_streams_json_frames(client: TestClient):
    with client.websocket_connect("/ws/metrics") as websocket:
        raw = websocket.receive_text()
        frame = json.loads(raw)
        assert "cpu_percent" in frame
        assert "memory_percent" in frame
        assert "disk_percent" in frame


def test_websocket_streams_at_one_second_interval(client: TestClient):
    with client.websocket_connect("/ws/metrics") as websocket:
        websocket.receive_text()
        start = time.monotonic()
        websocket.receive_text()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.9
