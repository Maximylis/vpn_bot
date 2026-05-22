import httpx

from app.config import settings


async def send_payment_success_message(
    telegram_id: int,
    expires_at: str,
) -> None:
    if not settings.bot_token:
        return

    text = (
        "✅ Оплата получена!\n\n"
        "Подписка активирована.\n"
        f"Доступ действует до: {expires_at}\n\n"
        "Чтобы получить VPN-конфиг, нажмите:\n"
        "🔐 Мой VPN-конфиг"
    )

    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{settings.bot_token}/sendMessage",
            json={
                "chat_id": telegram_id,
                "text": text,
            },
            timeout=10,
        )
