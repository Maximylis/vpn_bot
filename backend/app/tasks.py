import asyncio
import logging
from datetime import datetime, timezone

from app import models
from app.database import SessionLocal
from app.vpn_manager_client import delete_peer
from app.services.telegram_service import (
    send_trial_penultimate_day_notified_message,
    send_trial_lastday_message,
)


logger = logging.getLogger(__name__)


async def revoke_expired_access_once() -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    db = SessionLocal()
    try:
        expired_subscriptions = (
            db.query(models.Subscription)
            .filter(
                models.Subscription.status == "active",
                models.Subscription.expires_at <= now,
            )
            .all()
        )

        for subscription in expired_subscriptions:
            vpn_keys = (
                db.query(models.VpnKey)
                .filter(
                    models.VpnKey.user_id == subscription.user_id,
                    models.VpnKey.status == "active",
                )
                .all()
            )

            for vpn_key in vpn_keys:
                if vpn_key.peer_id:
                    try:
                        await delete_peer(vpn_key.peer_id)
                    except Exception as exc:
                        logger.exception(
                            "Failed to delete peer %s: %s",
                            vpn_key.peer_id,
                            exc,
                        )
                        continue

                vpn_key.status = "expired"
                vpn_key.revoked_at = now

            subscription.status = "expired"

        db.commit()

    except Exception:
        db.rollback()
        logger.exception("Failed to revoke expired access")
    finally:
        db.close()


async def revoke_expired_access_loop() -> None:
    while True:
        await revoke_expired_access_once()
        await asyncio.sleep(300)


async def send_trial_notifications_once() -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    db = SessionLocal()

    try:
        subscriptions = (
            db.query(models.Subscription)
            .filter(
                models.Subscription.status == "active",
                models.Subscription.is_trial.is_(True),
                models.Subscription.expires_at > now,
            )
            .all()
        )

        for subscription in subscriptions:
            user = subscription.user

            days_left = (
                subscription.expires_at.date() - now.date()
            ).days

            try:
                if (
                    days_left == 1
                    and not subscription.trial_3days_notified
                ):
                    await send_trial_penultimate_day_notified_message(
                        user.telegram_id
                    )
                    subscription.trial_penultimate_day_notified_notified = True

                if (
                    days_left == 0
                    and not subscription.trial_lastday_notified
                ):
                    await send_trial_lastday_message(user.telegram_id)
                    subscription.trial_lastday_notified = True

            except Exception:
                logger.exception(
                    "Failed to send trial notification to user %s",
                    user.telegram_id,
                )

        db.commit()

    except Exception:
        db.rollback()
        logger.exception("Failed to send trial notifications")

    finally:
        db.close()


async def send_trial_notifications_loop() -> None:
    while True:
        await send_trial_notifications_once()
        await asyncio.sleep(3600)
