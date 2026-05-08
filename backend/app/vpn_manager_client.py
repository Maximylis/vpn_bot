import httpx

from app.config import settings


async def create_peer(
    telegram_id: int,
    device_name: str = "default",
) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.vpn_manager_url}/peers",
            headers={
                "X-API-Token": settings.vpn_manager_api_token,
            },
            json={
                "telegram_id": telegram_id,
                "device_name": device_name,
            },
            timeout=30,
        )

        response.raise_for_status()

        return response.json()


async def delete_peer(peer_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{settings.vpn_manager_url}/peers/{peer_id}",
            headers={
                "X-API-Token": settings.vpn_manager_api_token,
            },
            timeout=30,
        )

        response.raise_for_status()

        return response.json()
