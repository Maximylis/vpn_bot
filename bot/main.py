import os
import io
import qrcode
from datetime import datetime

import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message, InlineKeyboardMarkup,
    InlineKeyboardButton, BufferedInputFile,
    CallbackQuery
)
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

if not API_TOKEN:
    raise RuntimeError("API_TOKEN is not set")


def api_headers() -> dict:
    return {
        "X-API-Token": API_TOKEN,
    }


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


main_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎁 Попробовать бесплатно 7 дней",
                callback_data="trial_7_days"
            )
        ],
        [
            InlineKeyboardButton(
                text="👤 Профиль",
                callback_data="profile"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔐 Мой VPN-конфиг",
                callback_data="my_vpn_config"
            )
        ],
    ]
)


def backend_post(path: str, json: dict | None = None):
    response = requests.post(
        f"{API_URL}{path}",
        json=json,
        headers=api_headers(),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def backend_get(path: str):
    response = requests.get(
        f"{API_URL}{path}",
        headers=api_headers(),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def format_datetime(value: str) -> str:
    dt = datetime.fromisoformat(value)
    return dt.strftime("%d.%m.%Y")


async def send_vpn_config_file(message: Message, config_text: str):
    file = BufferedInputFile(
        config_text.encode("utf-8"),
        filename="wg-vpn.conf",
    )

    await message.answer_document(
        document=file,
        caption=(
            "📄 Ваш WireGuard конфиг.\n\n"
            "Импортируйте файл в приложение WireGuard.")
    )


async def send_vpn_config_qr(
        message: Message, config_text: str
):
    img = qrcode.make(config_text)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    qr_file = BufferedInputFile(
        buffer.read(),
        filename="wg-vpn-qr.png",
    )

    await message.answer_photo(
        photo=qr_file,
        caption="📱 Отсканируйте QR-код в приложении WireGuard."
    )


@dp.message(Command("start"))
async def start_handler(message: Message):
    user = message.from_user

    payload = {
        "telegram_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }

    backend_post("/users", json=payload)

    await message.answer(
        "Добро пожаловать ✨\n\n"
        "Вы подключились к премиальному VPN-сервису 🔒\n"
        "⚡ Высокая скорость\n"
        "🌍 Доступ без ограничений\n"
        "🛡 Надежная защита данных\n"
        "Выберите действие ниже 👇\n",
        reply_markup=main_keyboard,
    )


@dp.message(Command("profile"))
async def profile_handler(message: Message):
    telegram_id = message.from_user.id

    access = backend_get(f"/users/{telegram_id}/access")

    if access["reason"] == "user_not_found":
        await message.answer(
            "Я пока не нашёл твой профиль.\n"
            "Нажми /start, чтобы зарегистрироваться."
        )
        return

    if not access["subscription"]:
        await message.answer(
            "Профиль найден, но активной подписки пока нет."
        )
        return

    subscription = access["subscription"]
    expires_at = format_datetime(subscription["expires_at"])
    access_status = "активен ✅" if access["has_access"] else "неактивен ❌"

    await message.answer(
        "👤 Профиль\n\n"
        f"Статус доступа: {access_status}\n"
        f"Подписка до: {expires_at}"
    )


@dp.message(Command("myvpn"))
async def myvpn_handler(message: Message):
    telegram_id = message.from_user.id

    access = backend_get(f"/users/{telegram_id}/access")

    if access["reason"] == "user_not_found":
        await message.answer(
            "Сначала нажми /start, чтобы зарегистрироваться."
        )
        return

    if access["reason"] == "no_active_subscription":
        await message.answer(
            "У тебя нет активной подписки."
        )
        return

    if access["reason"] == "no_active_vpn_keys":
        await message.answer(
            "Подписка активна, но VPN-ключ ещё не выдан."
        )
        return

    vpn_key = access["vpn_keys"][0]

    await message.answer("🔐 Твой VPN-конфиг:")
    await send_vpn_config_qr(message, vpn_key["config_text"])


@dp.message(F.text == "🎁 Попробовать бесплатно 7 дней")
async def trial_access_handler(message: Message):
    telegram_id = message.from_user.id

    try:
        result = backend_post(f"/dev/grant-access/{telegram_id}")

        if not result.get("ok"):
            if result.get("reason") == "trial_already_used":
                await message.answer(
                    "🎁 Бесплатный тестовый период уже был использован.\n\n"
                    "Текущий VPN-конфиг можно посмотреть через кнопку:\n"
                    "🔐 Мой VPN-конфиг"
                )
                return

        await message.answer("✅ Бесплатный доступ выдан на 7 дней!")
        await send_vpn_config_qr(message, result["vpn_key"]["config_text"])

    except requests.HTTPError as error:
        if error.response.status_code == 404:
            await message.answer(
                "Сначала нажми /start, чтобы зарегистрироваться."
            )
        else:
            await message.answer(
                "Не получилось выдать бесплатный доступ.\n"
                "Попробуй позже."
            )


@dp.message(F.text == "👤 Профиль")
async def profile_button_handler(message: Message):
    await profile_handler(message)


@dp.message(F.text == "🔐 Мой VPN-конфиг")
async def myvpn_button_handler(message: Message):
    await myvpn_handler(message)


@dp.callback_query(lambda c: c.data == "trial_7_days")
async def trial_7_days(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("🎁 Активируем пробный период на 7 дней")


@dp.callback_query(lambda c: c.data == "profile")
async def profile(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("👤 Ваш профиль")


@dp.callback_query(lambda c: c.data == "my_vpn_config")
async def my_vpn_config(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("🔐 Ваш VPN-конфиг")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
