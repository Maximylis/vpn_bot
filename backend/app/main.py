from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import Base, engine, get_db


app = FastAPI(title="VPN Bot Backend")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {
        "status": "ok",
        "db": result,
    }


@app.post("/init-db")
def init_db():
    Base.metadata.create_all(bind=engine)
    return {
        "status": "ok",
        "message": "Database tables created",
    }


@app.post("/users", response_model=schemas.UserRead)
def create_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    return crud.get_or_create_user(db, user_data)


@app.get("/users/{telegram_id}", response_model=schemas.UserRead | None)
def get_user(
    telegram_id: int,
    db: Session = Depends(get_db),
):
    return crud.get_user_by_telegram_id(db, telegram_id)


@app.post("/vpn-keys", response_model=schemas.VpnKeyRead)
def create_vpn_key(
    key_data: schemas.VpnKeyCreate,
    db: Session = Depends(get_db),
):
    return crud.create_vpn_key(db, key_data)


@app.get("/users/{user_id}/vpn-keys", response_model=list[schemas.VpnKeyRead])
def get_user_vpn_keys(
    user_id: int,
    db: Session = Depends(get_db),
):
    return crud.get_user_vpn_keys(db, user_id)


@app.post("/subscriptions", response_model=schemas.SubscriptionRead)
def create_subscription(
    subscription_data: schemas.SubscriptionCreate,
    db: Session = Depends(get_db),
):
    return crud.create_subscription(db, subscription_data)


@app.get("/users/{user_id}/subscription", response_model=schemas.SubscriptionRead | None)
def get_active_subscription(
    user_id: int,
    db: Session = Depends(get_db),
):
    return crud.get_active_subscription(db, user_id)

@app.get("/users/{telegram_id}/access", response_model=schemas.UserAccessRead)
def get_user_access(
    telegram_id: int,
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_telegram_id(db, telegram_id)

    if not user:
        return {
            "has_access": False,
            "reason": "user_not_found",
            "user": None,
            "subscription": None,
            "vpn_keys": [],
        }

    subscription = crud.get_valid_active_subscription(db, user.id)

    if not subscription:
        return {
            "has_access": False,
            "reason": "no_active_subscription",
            "user": user,
            "subscription": None,
            "vpn_keys": [],
        }

    vpn_keys = crud.get_active_vpn_keys(db, user.id)

    if not vpn_keys:
        return {
            "has_access": False,
            "reason": "no_active_vpn_keys",
            "user": user,
            "subscription": subscription,
            "vpn_keys": [],
        }

    return {
        "has_access": True,
        "reason": None,
        "user": user,
        "subscription": subscription,
        "vpn_keys": vpn_keys,
    }

@app.post("/dev/grant-access/{telegram_id}", response_model=schemas.GrantAccessRead)
def grant_access(
    telegram_id: int,
    db: Session = Depends(get_db),
):
    return crud.grant_test_access(db, telegram_id)
