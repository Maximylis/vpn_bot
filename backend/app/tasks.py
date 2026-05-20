import asyncio
import logging
from datetime import datetime, timezone

from app import models
from app.database import SessionLocal
from app.vpn_manager_client import delete_peer

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
