"""Unit tests for server health polling."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from api.models import Server
from api.poller import poll_server


def _mock_client(response=None, side_effect=None):
    client = AsyncMock()
    if side_effect:
        client.get = AsyncMock(side_effect=side_effect)
    else:
        client.get = AsyncMock(return_value=response)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.mark.asyncio
async def test_poll_server_sets_up_on_200():
    server = Server(id=1, name="api", host="10.0.0.1", port=8080)
    response = MagicMock()
    response.status_code = 200
    with patch("api.poller.httpx.AsyncClient", return_value=_mock_client(response)):
        await poll_server(server)
    assert server.status == "UP"


@pytest.mark.asyncio
async def test_poll_server_sets_degraded_on_non_200():
    server = Server(id=1, name="api", host="10.0.0.1", port=8080)
    response = MagicMock()
    response.status_code = 503
    with patch("api.poller.httpx.AsyncClient", return_value=_mock_client(response)):
        await poll_server(server)
    assert server.status == "DEGRADED"


@pytest.mark.asyncio
async def test_poll_server_sets_down_on_http_error():
    server = Server(id=1, name="api", host="10.0.0.1", port=8080)
    with patch(
        "api.poller.httpx.AsyncClient",
        return_value=_mock_client(side_effect=httpx.ConnectError("refused")),
    ):
        await poll_server(server)
    assert server.status == "DOWN"
