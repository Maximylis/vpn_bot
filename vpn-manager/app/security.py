from fastapi import Header, HTTPException, status

from app.config import settings


async def verify_api_token(x_api_token: str = Header(...)) -> None:
    if x_api_token != settings.vpn_manager_api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
        )
