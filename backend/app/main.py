import asyncio

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from decimal import Decimal

from app import crud, schemas
from app.config import settings
from app.database import Base, engine, get_db
from app.security import verify_api_token
from app.tasks import (
    revoke_expired_access_loop,
    send_trial_notifications_loop,
)
from app.tariffs import TARIFFS
from app.services.yookassa_service import (
    create_yookassa_payment,
    get_yookassa_payment,
)


app = FastAPI(title="VPN Bot Backend")


@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(revoke_expired_access_loop())
    asyncio.create_task(send_trial_notifications_loop())


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/db-check")
async def db_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {
        "status": "ok",
        "db": result,
    }


@app.post("/init-db", dependencies=[Depends(verify_api_token)])
async def init_db():
    Base.metadata.create_all(bind=engine)
    return {
        "status": "ok",
        "message": "Database tables created",
    }


@app.post("/users", response_model=schemas.UserRead)
async def create_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    return crud.get_or_create_user(db, user_data)


@app.get("/users/{telegram_id}", response_model=schemas.UserRead | None)
async def get_user(
    telegram_id: int,
    db: Session = Depends(get_db),
):
    return crud.get_user_by_telegram_id(db, telegram_id)


@app.post("/vpn-keys", response_model=schemas.VpnKeyRead)
async def create_vpn_key(
    key_data: schemas.VpnKeyCreate,
    db: Session = Depends(get_db),
):
    return crud.create_vpn_key(db, key_data)


@app.get("/users/{user_id}/vpn-keys", response_model=list[schemas.VpnKeyRead])
async def get_user_vpn_keys(
    user_id: int,
    db: Session = Depends(get_db),
):
    return crud.get_user_vpn_keys(db, user_id)


@app.post("/subscriptions", response_model=schemas.SubscriptionRead)
async def create_subscription(
    subscription_data: schemas.SubscriptionCreate,
    db: Session = Depends(get_db),
):
    return crud.create_subscription(db, subscription_data)


@app.get(
    "/users/{user_id}/subscription",
    response_model=schemas.SubscriptionRead | None,
)
async def get_active_subscription(
    user_id: int,
    db: Session = Depends(get_db),
):
    return crud.get_active_subscription(db, user_id)


@app.get(
    "/users/{telegram_id}/access",
    response_model=schemas.UserAccessRead,
    dependencies=[Depends(verify_api_token)],
)
async def get_user_access(
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


if settings.app_env == "development":
    @app.post(
        "/dev/grant-access/{telegram_id}",
        response_model=schemas.GrantAccessRead,
        dependencies=[Depends(verify_api_token)],
    )
    async def grant_access(
        telegram_id: int,
        db: Session = Depends(get_db),
    ):
        result = await crud.grant_test_access(
            db=db,
            telegram_id=telegram_id,
            days=7,
        )

        if not result["ok"]:
            return result

        return result


@app.post(
    "/payments/create",
    response_model=schemas.PaymentCreateResponse,
    dependencies=[Depends(verify_api_token)],
)
async def create_payment(
    payment_data: schemas.PaymentCreateRequest,
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_telegram_id(
        db,
        payment_data.telegram_id,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    tariff = TARIFFS.get(payment_data.tariff)

    if not tariff:
        raise HTTPException(
            status_code=400,
            detail="Invalid tariff",
        )

    yookassa_payment = create_yookassa_payment(
        amount=tariff["amount"],
        description=tariff["title"],
        telegram_id=user.telegram_id,
        tariff=payment_data.tariff,
    )

    payment = crud.create_payment(
        db=db,
        user_id=user.id,
        tariff=payment_data.tariff,
        amount=Decimal(tariff["amount"]),
        yookassa_payment_id=yookassa_payment.id,
        confirmation_url=(
            yookassa_payment.confirmation.confirmation_url
        ),
    )

    return {
        "ok": True,
        "payment_id": payment.id,
        "yookassa_payment_id": yookassa_payment.id,
        "confirmation_url": (
            yookassa_payment.confirmation.confirmation_url
        ),
    }


@app.post("/payments/yookassa/webhook")
async def yookassa_webhook(
    webhook_data: schemas.YookassaWebhookRequest,
    db: Session = Depends(get_db),
):
    if webhook_data.event != "payment.succeeded":
        return {
            "ok": True,
            "ignored": True,
            "event": webhook_data.event,
        }

    payment = crud.get_payment_by_yookassa_id(
        db=db,
        yookassa_payment_id=webhook_data.object.id,
    )

    if not payment:
        return {
            "ok": False,
            "reason": "payment_not_found",
        }

    tariff = TARIFFS.get(payment.tariff)

    if not tariff:
        return {
            "ok": False,
            "reason": "invalid_tariff",
        }

    yookassa_payment = get_yookassa_payment(webhook_data.object.id)

    payment_method_id = None

    if yookassa_payment.payment_method:
        payment_method_saved = getattr(
            yookassa_payment.payment_method,
            "saved",
            False,
        )

        if payment_method_saved:
            payment_method_id = getattr(
                yookassa_payment.payment_method,
                "id",
                None,
            )

    result = await crud.activate_paid_subscription(
        db=db,
        payment=payment,
        months=tariff["months"],
        payment_method_id=payment_method_id,
    )

    return result
