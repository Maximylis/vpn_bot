import uuid

from fastapi import Depends, FastAPI

from app.schemas import (
    CreatePeerRequest,
    CreatePeerResponse,
    DeletePeerResponse,
)
from app.security import verify_api_token

app = FastAPI(title="VPN Manager")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/protected-health", dependencies=[Depends(verify_api_token)])
async def protected_health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/peers",
    response_model=CreatePeerResponse,
    dependencies=[Depends(verify_api_token)],
)
async def create_peer(
    request: CreatePeerRequest,
) -> CreatePeerResponse:
    peer_id = str(uuid.uuid4())

    config = f"""
[Interface]
PrivateKey = mock-private-key
Address = 10.0.0.2/32
DNS = 1.1.1.1

[Peer]
PublicKey = mock-server-public-key
Endpoint = 127.0.0.1:51820
AllowedIPs = 0.0.0.0/0
"""

    return CreatePeerResponse(
        peer_id=peer_id,
        config=config.strip(),
    )


@app.delete(
    "/peers/{peer_id}",
    response_model=DeletePeerResponse,
    dependencies=[Depends(verify_api_token)],
)
async def delete_peer(peer_id: str) -> DeletePeerResponse:
    return DeletePeerResponse(success=True)
