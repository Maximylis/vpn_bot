from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from decimal import Decimal
from dateutil.relativedelta import relativedelta

from app import models, schemas
from app.vpn_manager_client import create_peer
from app.services.telegram_service import send_payment_success_message


def get_user_by_telegram_id(
    db: Session,
    telegram_id: int,
) -> models.User | None:
    return (
        db.query(models.User)
        .filter(models.User.telegram_id == telegram_id)
        .first()
    )


def create_user(db: Session, user_data: schemas.UserCreate) -> models.User:
    user = models.User(**user_data.model_dump())

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_or_create_user(
    db: Session,
    user_data: schemas.UserCreate,
) -> models.User:
    user = get_user_by_telegram_id(db, user_data.telegram_id)

    if user:
        return user

    return create_user(db, user_data)


def create_vpn_key(
    db: Session,
    key_data: schemas.VpnKeyCreate,
) -> models.VpnKey:
    vpn_key = models.VpnKey(**key_data.model_dump())

    db.add(vpn_key)
    db.commit()
    db.refresh(vpn_key)

    return vpn_key


def get_user_vpn_keys(db: Session, user_id: int) -> list[models.VpnKey]:
    return (
        db.query(models.VpnKey)
        .filter(models.VpnKey.user_id == user_id)
        .order_by(models.VpnKey.created_at.desc())
        .all()
    )


def create_subscription(
    db: Session,
    subscription_data: schemas.SubscriptionCreate,
) -> models.Subscription:
    subscription = models.Subscription(**subscription_data.model_dump())

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription


def get_active_subscription(
    db: Session,
    user_id: int,
) -> models.Subscription | None:
    return (
        db.query(models.Subscription)
        .filter(
            models.Subscription.user_id == user_id,
            models.Subscription.status == "active",
        )
        .order_by(models.Subscription.expires_at.desc())
        .first()
    )


def get_active_vpn_keys(db: Session, user_id: int) -> list[models.VpnKey]:
    return (
        db.query(models.VpnKey)
        .filter(
            models.VpnKey.user_id == user_id,
            models.VpnKey.status == "active",
        )
        .order_by(models.VpnKey.created_at.desc())
        .all()
    )


def get_valid_active_subscription(
    db: Session,
    user_id: int,
) -> models.Subscription | None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    return (
        db.query(models.Subscription)
        .filter(
            models.Subscription.user_id == user_id,
            models.Subscription.status == "active",
            models.Subscription.starts_at <= now,
            models.Subscription.expires_at > now,
        )
        .order_by(models.Subscription.expires_at.desc())
        .first()
    )


async def grant_test_access(
    db: Session,
    telegram_id: int,
    days: int = 7,
) -> dict:
    user = get_user_by_telegram_id(db, telegram_id)

    if not user:
        return {
            "ok": False,
            "reason": "user_not_found",
        }

    existing_subscription = (
        db.query(models.Subscription)
        .filter(models.Subscription.user_id == user.id)
        .first()
    )

    if existing_subscription:
        return {
            "ok": False,
            "reason": "trial_already_used",
        }

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + timedelta(days=days)

    subscription = (
        db.query(models.Subscription)
        .filter(
            models.Subscription.user_id == user.id,
            models.Subscription.status == "active",
        )
        .order_by(models.Subscription.expires_at.desc())
        .first()
    )

    if subscription:
        subscription.starts_at = now
        subscription.expires_at = expires_at
    else:
        subscription = models.Subscription(
            user_id=user.id,
            status="active",
            starts_at=now,
            expires_at=expires_at,
            is_trial=True,
        )
        db.add(subscription)

    vpn_key = (
        db.query(models.VpnKey)
        .filter(
            models.VpnKey.user_id == user.id,
            models.VpnKey.provider == "wireguard",
            models.VpnKey.status == "active",
        )
        .order_by(models.VpnKey.created_at.desc())
        .first()
    )

    if vpn_key is None:
        peer = await create_peer(telegram_id=telegram_id)

        vpn_key = models.VpnKey(
            user_id=user.id,
            provider="wireguard",
            key_name=f"{telegram_id}.conf",
            peer_id=peer["peer_id"],
            config_text=peer["config"],
            status="active",
        )
        db.add(vpn_key)

    db.commit()

    db.refresh(subscription)
    db.refresh(vpn_key)

    return {
        "ok": True,
        "user": user,
        "subscription": subscription,
        "vpn_key": vpn_key,
    }


def create_payment(
    db: Session,
    user_id: int,
    tariff: str,
    amount: Decimal,
    yookassa_payment_id: str,
    confirmation_url: str,
) -> models.Payment:
    payment = models.Payment(
        user_id=user_id,
        tariff=tariff,
        amount=amount,
        status=models.PaymentStatus.pending.value,
        yookassa_payment_id=yookassa_payment_id,
        confirmation_url=confirmation_url,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


def get_payment_by_yookassa_id(
    db: Session,
    yookassa_payment_id: str,
) -> models.Payment | None:
    return (
        db.query(models.Payment)
        .filter(models.Payment.yookassa_payment_id == yookassa_payment_id)
        .first()
    )


async def activate_paid_subscription(
    db: Session,
    payment: models.Payment,
    months: int,
    payment_method_id: str | None = None,
) -> dict:
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if payment.status == models.PaymentStatus.succeeded.value:
        return {
            "ok": True,
            "reason": "already_activated",
        }

    user = payment.user

    subscription = get_valid_active_subscription(db, user.id)

    if subscription:
        subscription.expires_at = subscription.expires_at + relativedelta(
            months=months
        )
        subscription.is_trial = False
        subscription.trial_penultimate_day_notified = True
        subscription.trial_lastday_notified = True
    else:
        subscription = models.Subscription(
            user_id=user.id,
            status=models.SubscriptionStatus.active.value,
            starts_at=now,
            expires_at=now + relativedelta(months=months),
            is_trial=False,
            trial_penultimate_day_notified=True,
            trial_lastday_notified=True,
        )
        db.add(subscription)

    if payment_method_id:
        subscription.auto_renew = True
        subscription.payment_method_id = payment_method_id

    vpn_key = (
        db.query(models.VpnKey)
        .filter(
            models.VpnKey.user_id == user.id,
            models.VpnKey.provider == "wireguard",
            models.VpnKey.status == "active",
        )
        .order_by(models.VpnKey.created_at.desc())
        .first()
    )

    if vpn_key is None:
        peer = await create_peer(telegram_id=user.telegram_id)

        vpn_key = models.VpnKey(
            user_id=user.id,
            provider="wireguard",
            key_name=f"{user.telegram_id}.conf",
            peer_id=peer["peer_id"],
            config_text=peer["config"],
            status=models.VpnKeyStatus.active.value,
        )
        db.add(vpn_key)

    payment.status = models.PaymentStatus.succeeded.value
    payment.paid_at = now

    db.commit()

    await send_payment_success_message(
        telegram_id=user.telegram_id,
        expires_at=subscription.expires_at.strftime("%d.%m.%Y"),
    )

    return {
        "ok": True,
        "reason": "activated",
    }
