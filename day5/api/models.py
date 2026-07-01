"""Server dataclass and Pydantic schemas."""

from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass
class Server:
    """Registered server with polling status."""

    id: int
    name: str
    host: str
    port: int
    status: str = "UNKNOWN"

    def base_url(self) -> str:
        """HTTP base URL for health checks."""
        return f"http://{self.host}:{self.port}"


class ServerIn(BaseModel):
    """Payload to register a new server."""

    name: str = Field(..., min_length=1)
    host: str = Field(..., min_length=1)
    port: int = Field(..., ge=1, le=65535)


class ServerOut(BaseModel):
    """Server returned by the API."""

    id: int
    name: str
    host: str
    port: int
    status: str
