from fastapi import Header, HTTPException, status

from app.config import settings


async def verify_api_token(
        x_api_token: str | None = Header(default=None)
) -> None:
    if not settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_TOKEN is not configured",
        )

    if x_api_token != settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
        )
