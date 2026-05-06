from sqlalchemy.orm import Session

from datetime import datetime, timedelta, timezone

from app import models, schemas


def get_user_by_telegram_id(db: Session, telegram_id: int) -> models.User | None:
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


def get_or_create_user(db: Session, user_data: schemas.UserCreate) -> models.User:
    user = get_user_by_telegram_id(db, user_data.telegram_id)

    if user:
        return user

    return create_user(db, user_data)


def create_vpn_key(db: Session, key_data: schemas.VpnKeyCreate) -> models.VpnKey:
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

def grant_test_access(
    db: Session,
    telegram_id: int,
    days: int = 30,
) -> dict:
    user = get_user_by_telegram_id(db, telegram_id)

    if not user:
        return {
            "ok": False,
            "reason": "user_not_found",
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
        )
        db.add(subscription)

    vpn_key = (
        db.query(models.VpnKey)
        .filter(
            models.VpnKey.user_id == user.id,
            models.VpnKey.provider == "dev",
            models.VpnKey.status == "active",
        )
        .order_by(models.VpnKey.created_at.desc())
        .first()
    )

    if vpn_key:
        vpn_key.key_name = f"{telegram_id}.conf"
        vpn_key.config_text = f"{telegram_id}.conf"
    else:
        vpn_key = models.VpnKey(
            user_id=user.id,
            provider="dev",
            key_name=f"{telegram_id}.conf",
            config_text=f"{telegram_id}.conf",
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
