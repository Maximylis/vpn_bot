from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine


app = FastAPI(
    title="VPN Bot Backend",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "vpn-bot-backend",
    }


@app.get("/db-check")
def db_check():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "status": "ok",
        "database": "connected",
        "result": value,
    }
