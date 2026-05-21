import os
import io
import qrcode
from datetime import datetime

import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
    CallbackQuery,
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


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


main_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎁 Попробовать бесплатно 7 дней",
                callback_data="trial_7_days",
            )
        ],
        [
            InlineKeyboardButton(
                text="📲 Как подключить?",
                callback_data="how_to_connect"
            )
        ],
        [
            InlineKeyboardButton(
                text="🚀 Тарифы 🚀",
                callback_data="tariffs"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔐 Мой VPN-конфиг",
                callback_data="my_vpn_config",
            )
        ],
        [
            InlineKeyboardButton(
                text="ℹ️ Информация",
                callback_data="info",
            ),
            InlineKeyboardButton(
                text="👤 Профиль",
                callback_data="profile",
            )
        ],
    ]
)


info_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📜 Пользовательское соглашение",
                url="https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19",
            )
        ],
        [
            InlineKeyboardButton(
                text="🔒 Политика конфиденциальности",
                url="https://telegra.ph/Politika-konfidencialnosti-04-01-26",
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="delete_message",
            )
        ],
    ]
)


how_to_connect_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📱 Телефон",
                callback_data="instruction_phone"
            )
        ],
        [
            InlineKeyboardButton(
                text="💻 Компьютер",
                callback_data="instruction_computer"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="delete_message"
            )
        ]
    ]
)


tariffs_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="1️⃣ месяц - 349₽",
                callback_data="one_month"
            )
        ],
        [
            InlineKeyboardButton(
                text="3️⃣ месяца - 889₽ -15%🔻",
                callback_data="three_month"
            )
        ],
        [
            InlineKeyboardButton(
                text="6️⃣ месяцев - 1.675₽ -20%🔻",
                callback_data="six_month"
            )
        ],
        [
            InlineKeyboardButton(
                text="1️⃣2️⃣ месяцев - 2.999₽ -30%🔻",
                callback_data="twelth_month"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="delete_message"
            )
        ]
    ]
)


vpn_config_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📷 QR-код",
                callback_data="vpn_qr"
            )
        ],
        [
            InlineKeyboardButton(
                text="📄 Файл .conf",
                callback_data="vpn_file"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="delete_message"
            )
        ]
    ]
)


back_delete_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="delete_message",
            )
        ],
    ]
)


INFO_TEXT = (
    "ℹ️ Информация о VPN_AXM\n\n"
    "VPN_AXM — сервис для быстрого и безопасного "
    "подключения через WireGuard.\n\n"
    "🔒 Защита интернет-соединения\n"
    "⚡ Быстрое подключение\n"
    "🌍 Доступ без ограничений\n"
    "📱 Поддержка телефона и компьютера\n\n"
    "☎️ Служба поддержки: @AXMbotsupport\n\n"
    "Ниже можно открыть пользовательское соглашение."
)


def api_headers() -> dict:
    return {
        "X-API-Token": API_TOKEN,
    }


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


async def send_vpn_config_file(
        message: Message,
        config_text: str,
        reply_markup=None
):
    file = BufferedInputFile(
        config_text.encode("utf-8"),
        filename="wg-vpn.conf",
    )

    await message.answer_document(
        document=file,
        caption=(
            "📄 Ваш WireGuard конфиг.\n\n"
            "Импортируйте файл в приложение WireGuard."
        ),
        reply_markup=reply_markup
    )


async def send_vpn_config_qr(
        message: Message,
        config_text: str,
        reply_markup=None
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
        caption="📱 Отсканируйте QR-код в приложении WireGuard.",
        reply_markup=reply_markup
    )


async def show_profile(
        message: Message,
        telegram_id: int,
        reply_markup=None
):
    access = backend_get(f"/users/{telegram_id}/access")

    if access["reason"] == "user_not_found":
        await message.answer(
            "Я пока не нашёл твой профиль.\n"
            "Нажми /start, чтобы зарегистрироваться.",
            reply_markup=reply_markup
        )
        return

    if not access["subscription"]:
        await message.answer(
            "Профиль найден, но активной подписки пока нет.",
            reply_markup=reply_markup
        )
        return

    subscription = access["subscription"]
    expires_at = format_datetime(subscription["expires_at"])
    access_status = "активен ✅" if access["has_access"] else "неактивен ❌"

    await message.answer(
        "👤 Профиль\n\n"
        f"Статус доступа: {access_status}\n"
        f"Подписка до: {expires_at}",
        reply_markup=reply_markup
    )


async def show_myvpn(
        message: Message,
        telegram_id: int,
        config_format: str,
        reply_markup=None
):
    access = backend_get(f"/users/{telegram_id}/access")

    if access["reason"] == "user_not_found":
        await message.answer(
            "Сначала нажми /start, чтобы зарегистрироваться.",
            reply_markup=reply_markup
        )
        return

    if access["reason"] == "no_active_subscription":
        await message.answer(
            "🚫 У тебя нет активной подписки. 🚫",
            reply_markup=reply_markup
        )
        return

    if access["reason"] == "no_active_vpn_keys":
        await message.answer(
            "Подписка активна, но VPN-ключ ещё не выдан.",
            reply_markup=reply_markup
        )
        return

    vpn_key = access["vpn_keys"][0]

    if config_format == "qr":
        await send_vpn_config_qr(
            message,
            vpn_key["config_text"],
            reply_markup=reply_markup
        )

    if config_format == "file":
        await send_vpn_config_file(
            message,
            vpn_key["config_text"],
            reply_markup=reply_markup
        )


async def grant_trial_access(
        message: Message,
        telegram_id: int,
        reply_markup=None
):
    try:
        result = backend_post(f"/dev/grant-access/{telegram_id}")

        if not result.get("ok"):
            if result.get("reason") == "trial_already_used":
                await message.answer(
                    "🎁 Бесплатный тестовый период уже был использован.\n\n"
                    "Текущий VPN-конфиг можно посмотреть через кнопку:\n"
                    "🔐 Мой VPN-конфиг",
                    reply_markup=reply_markup
                )
                return

            await message.answer(
                "Не получилось выдать бесплатный доступ.\n"
                "Попробуй позже.",
                reply_markup=reply_markup
            )
            return

        await message.answer(
            "✅ Бесплатный доступ выдан на 7 дней!\n\n"
            "Инструкция по подключению посмотреть через кнопку:\n\n"
            "📲 Как подключить?\n\n"
            "Получить VPN  через кнопку:\n\n"
            "🔐 Мой VPN-конфиг",
            reply_markup=reply_markup
        )

    except requests.HTTPError as error:
        if error.response.status_code == 404:
            await message.answer(
                "Сначала нажми /start, чтобы зарегистрироваться."
            )
        else:
            await message.answer(
                "Не получилось выдать бесплатный доступ.\n"
                "Попробуй позже.",
                reply_markup=reply_markup
            )
а 

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
        "🛡 Надежная защита данных\n\n"
        "Выберите действие ниже 👇",
        reply_markup=main_keyboard,
    )


@dp.message(Command("profile"))
async def profile_handler(message: Message):
    await show_profile(
        message=message,
        telegram_id=message.from_user.id,
        reply_markup=back_delete_keyboard
    )


@dp.message(Command("myvpn"))
async def myvpn_handler(message: Message):
    await show_myvpn(
        message=message,
        telegram_id=message.from_user.id,
        reply_markup=back_delete_keyboard
    )


@dp.message(F.text == "🎁 Попробовать бесплатно 7 дней")
async def trial_access_button_handler(message: Message):
    await grant_trial_access(
        message=message,
        telegram_id=message.from_user.id,
        reply_markup=back_delete_keyboard
    )


@dp.message(F.text == "👤 Профиль")
async def profile_button_handler(message: Message):
    await show_profile(
        message=message,
        telegram_id=message.from_user.id,
        reply_markup=back_delete_keyboard
    )


@dp.message(F.text == "🔐 Мой VPN-конфиг")
async def myvpn_button_handler(message: Message):
    await show_myvpn(
        message=message,
        telegram_id=message.from_user.id,
        reply_markup=back_delete_keyboard
    )


@dp.callback_query(F.data == "info")
async def info_callback(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        INFO_TEXT,
        reply_markup=info_keyboard
    )


@dp.callback_query(F.data == "delete_message")
async def delete_message_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()


@dp.callback_query(F.data == "trial_7_days")
async def trial_7_days_callback(callback: CallbackQuery):
    await callback.answer()

    await grant_trial_access(
        message=callback.message,
        telegram_id=callback.from_user.id,
        reply_markup=back_delete_keyboard
    )


@dp.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery):
    await callback.answer()

    await show_profile(
        message=callback.message,
        telegram_id=callback.from_user.id,
        reply_markup=back_delete_keyboard
    )


@dp.callback_query(F.data == "my_vpn_config")
async def my_vpn_config_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🔐 Выберите формат VPN-конфига:",
        reply_markup=vpn_config_keyboard
    )


@dp.callback_query(F.data == "vpn_qr")
async def vpn_qr_callback(callback: CallbackQuery):
    await callback.answer()

    await show_myvpn(
        message=callback.message,
        telegram_id=callback.from_user.id,
        config_format="qr",
        reply_markup=back_delete_keyboard
    )


@dp.callback_query(F.data == "vpn_file")
async def vpn_file_callback(callback: CallbackQuery):
    await callback.answer()

    await show_myvpn(
        message=callback.message,
        telegram_id=callback.from_user.id,
        config_format="file",
        reply_markup=back_delete_keyboard
    )


@dp.callback_query(F.data == "tariffs")
async def tariffs_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "📆 Здесь вы можете выбрать подходящий тариф:",
        reply_markup=tariffs_keyboard
    )


@dp.callback_query(F.data == "how_to_connect")
async def how_to_connect_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "📲 Выберите устройство:",
        reply_markup=how_to_connect_keyboard
    )


@dp.callback_query(F.data == "instruction_phone")
async def instruction_phone_callback(callback: CallbackQuery):
    await callback.answer()
    photo = BufferedInputFile(
        open("assets/phone.png", "rb").read(),
        filename="phone.png"
    )
    await callback.message.answer_photo(
        photo=photo,
        caption=(
            "📱 Инструкция для подключения VPN на телефоне.\n\n"
            "1. Установите приложение WireGuard:\n"
            '<a href="https://apps.apple.com/app/wireguard/id1441195209">'
            "Скачать приложение на iOS</a>\n"
            '<a href="https://play.google.com/store/apps/details?'
            'id=com.wireguard.android">'
            "Скачать на Android</a>\n\n"
            "2. После покупки вы получите конфигурацию WireGuard.\n"
            "3. Добавьте конфигурацию через QR-код или файл."
        ),
        parse_mode="HTML",
        reply_markup=back_delete_keyboard
    )


@dp.callback_query(F.data == "instruction_computer")
async def instruction_computer_callback(callback: CallbackQuery):
    await callback.answer()
    photo = BufferedInputFile(
        open("assets/computer.png", "rb").read(),
        filename="computer.png"
    )
    await callback.message.answer_photo(
        photo=photo,
        caption=(
            "💻 Инструкция для подключения VPN на компьютере.\n\n"
            "1. Установите приложение WireGuard:\n"
            '<a href="https://www.wireguard.com/install/">'
            "Скачать WireGuard для компьютера</a>\n\n"
            "2. После покупки вы получите конфигурационный файл WireGuard.\n"
            "3. Импортируйте файл в приложение."
        ),
        parse_mode="HTML",
        reply_markup=back_delete_keyboard
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
