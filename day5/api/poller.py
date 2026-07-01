"""Async health polling for registered servers."""

import asyncio
import logging

import httpx

from api.models import Server

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 10
HEALTH_TIMEOUT_SECONDS = 3.0


async def poll_server(server: Server) -> None:
    """Check GET /health and update server status."""
    url = f"{server.base_url()}/health"
    try:
        async with httpx.AsyncClient(timeout=HEALTH_TIMEOUT_SECONDS) as client:
            response = await client.get(url)
        if response.status_code == 200:
            server.status = "UP"
        else:
            server.status = "DEGRADED"
    except httpx.HTTPError as exc:
        logger.debug("Poll failed for %s: %s", server.name, exc)
        server.status = "DOWN"


async def run_poll_loop(servers: dict[int, Server]) -> None:
    """Poll all servers every 10 seconds until cancelled."""
    while True:
        if servers:
            await asyncio.gather(*(poll_server(s) for s in servers.values()))
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
