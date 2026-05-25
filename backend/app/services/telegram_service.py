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


async def send_trial_penultimate_day_notified_message(
        telegram_id: int
) -> None:
    if not settings.bot_token:
        return

    text = (
        "Привет! 👋\n"
        "Говорят:\n"
        "— человек может прожить 3 недели без еды 🍔"
        "— 3 дня без воды 💧"
        "— 3 минуты без воздуха 🌬"
        "Но вот без стабильного и безопасного интернета — !!!0!!! 😅"
        "ЗАВТРА твоя пробная подписка на VPN заканчивается."
        "Чтобы и дальше смотреть, работать, общаться без ограничений и лишних "
        "глаз 👀 — продли доступ прямо сейчас.\n\n"
        "Не оставайся без защиты и связи."
        "Подключай VPN и оставайся онлайн без границ 🚀"
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


async def send_trial_lastday_message(telegram_id: int) -> None:
    if not settings.bot_token:
        return

    text = (
        "⚠️ Сегодня последний день бесплатного VPN.\n\n"
        "Чтобы VPN продолжил работать без перерыва, оформи подписку "
        "в разделе «🚀 Тарифы 🚀»."
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
