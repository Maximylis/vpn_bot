import uuid

from fastapi import Depends, FastAPI, HTTPException, status

from app.schemas import (
    CreatePeerRequest,
    CreatePeerResponse,
    DeletePeerResponse,
)
from app.config import settings
from app.wireguard import (
    allocate_client_ip,
    generate_private_key,
    generate_public_key,
    WireGuardError,
    add_peer,
    remove_peer,
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

    private_key = generate_private_key()
    public_key = generate_public_key(private_key)

    client_ip = allocate_client_ip()
    add_peer(peer_id=peer_id, public_key=public_key, client_ip=client_ip)

    config = f"""
[Interface]
PrivateKey = {private_key}
Address = {client_ip}
DNS = {settings.wg_client_dns}

[Peer]
PublicKey = {settings.wg_server_public_key}
Endpoint = {settings.wg_endpoint}
AllowedIPs = {settings.wg_client_allowed_ips}
PersistentKeepalive = 25
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
    try:
        deleted = remove_peer(peer_id)
    except WireGuardError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Peer not found",
        )

    return DeletePeerResponse(success=True)
