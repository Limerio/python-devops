"""DevOps Monitoring API — FastAPI application."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from api.auth import verify_api_key
from api.metrics import get_system_metrics
from api.models import Server, ServerIn, ServerOut
from api.poller import poll_server, run_poll_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

_servers: dict[int, Server] = {}
_next_id = 1
_poll_task: asyncio.Task | None = None


def _server_to_out(server: Server) -> ServerOut:
    return ServerOut(
        id=server.id,
        name=server.name,
        host=server.host,
        port=server.port,
        status=server.status,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background polling on startup."""
    global _poll_task
    _poll_task = asyncio.create_task(run_poll_loop(_servers))
    logger.info("Poll loop started")
    yield
    if _poll_task:
        _poll_task.cancel()
        try:
            await _poll_task
        except asyncio.CancelledError:
            pass
    logger.info("Poll loop stopped")


app = FastAPI(title="DevOps Monitoring API", lifespan=lifespan)


@app.get("/health")
async def health():
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    """Current system metrics snapshot."""
    return get_system_metrics()


@app.get("/servers", response_model=list[ServerOut])
async def list_servers():
    """List registered servers and their polling status."""
    return [_server_to_out(s) for s in _servers.values()]


@app.post("/servers", response_model=ServerOut, status_code=status.HTTP_201_CREATED)
async def create_server(
    payload: ServerIn,
    _: Annotated[str, Depends(verify_api_key)],
):
    """Register a new server (requires API key)."""
    global _next_id
    server = Server(
        id=_next_id,
        name=payload.name,
        host=payload.host,
        port=payload.port,
        status="UNKNOWN",
    )
    _servers[_next_id] = server
    _next_id += 1
    await poll_server(server)
    return _server_to_out(server)


@app.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: int,
    _: Annotated[str, Depends(verify_api_key)],
):
    """Remove a server (requires API key)."""
    if server_id not in _servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    del _servers[server_id]


@app.post("/servers/{server_id}/check", response_model=ServerOut)
async def check_server(
    server_id: int,
    _: Annotated[str, Depends(verify_api_key)],
):
    """Trigger an immediate health check (requires API key)."""
    if server_id not in _servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    server = _servers[server_id]
    await poll_server(server)
    return _server_to_out(server)


@app.websocket("/ws/metrics")
async def ws_metrics(websocket: WebSocket):
    """Stream system metrics as JSON every second."""
    await websocket.accept()
    try:
        while True:
            payload = get_system_metrics()
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
