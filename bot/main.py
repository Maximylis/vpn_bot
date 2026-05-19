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
                text="📄 Пользовательское соглашение",
                callback_data="user_agreement",
            )
        ],
    ]
)


# ДОБАВЛЕНО: кнопка назад под соглашением
agreement_keyboard = InlineKeyboardMarkup(
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
    "VPN_AXM — сервис для быстрого и безопасного подключения через WireGuard.\n\n"
    "🔒 Защита интернет-соединения\n"
    "⚡ Быстрое подключение\n"
    "🌍 Доступ без ограничений\n"
    "📱 Поддержка телефона и компьютера\n\n"
    "Ниже можно открыть пользовательское соглашение."
)


# ИЗМЕНЕНО: вставлен полный текст пользовательского соглашения
USER_AGREEMENT_TEXT = (
    "📜 Пользовательское соглашение\n\n"
    "Дата вступления в силу: 17.05.2026\n"
    "Последнее обновление: 17.05.2026\n\n"
    "Настоящее Пользовательское соглашение (далее — «Соглашение») регулирует "
    "порядок использования сервиса Anyport VPN (далее — «Сервис»). Используя "
    "Сервис, пользователь подтверждает согласие с условиями настоящего Соглашения.\n\n"

    "1. Общие положения\n"
    "• Сервис предоставляет пользователям программный доступ к VPN-подключению "
    "для повышения безопасности и конфиденциальности интернет-соединения.\n"
    "• Доступ к Сервису предоставляется на платной основе в формате подписки "
    "на определённый срок.\n"
    "• Использование Сервиса допускается исключительно в законных целях.\n"
    "• Использование Сервиса означает полное и безоговорочное принятие условий "
    "настоящего Соглашения.\n\n"

    "2. Предоставление услуг\n"
    "• После успешной оплаты пользователь получает доступ к функционалу Сервиса "
    "автоматически либо в течение разумного технического времени.\n"
    "• Услуга считается оказанной с момента предоставления доступа к Сервису.\n"
    "• Срок действия подписки определяется выбранным тарифом.\n\n"

    "3. Обязанности пользователя\n"
    "Пользователь обязуется:\n"
    "• не использовать Сервис для нарушения законодательства;\n"
    "• не распространять вредоносное программное обеспечение, спам, запрещённый контент;\n"
    "• не предпринимать действий, нарушающих работоспособность Сервиса;\n"
    "• соблюдать законодательство страны использования Сервиса.\n\n"

    "4. Права пользователя\n"
    "Пользователь имеет право:\n"
    "• использовать Сервис в течение оплаченного периода;\n"
    "• обращаться в службу технической поддержки;\n"
    "• запросить возврат денежных средств в соответствии с политикой возврата;\n"
    "• получать информацию об изменениях условий использования Сервиса.\n\n"

    "5. Оплата и возврат средств\n"
    "• Оплата услуг осуществляется через сторонние платёжные системы.\n"
    "• Сервис не хранит данные банковских карт пользователей.\n"
    "• Возврат денежных средств рассматривается индивидуально при наличии "
    "подтверждённых технических проблем, препятствующих использованию Сервиса.\n"
    "• Возврат не осуществляется в случае:\n"
    "— окончания оплаченного периода подписки;\n"
    "— нарушения пользователем условий настоящего Соглашения;\n"
    "— невозможности использования Сервиса по причинам, не зависящим от Сервиса.\n\n"

    "6. Ограничение ответственности\n"
    "• Сервис предоставляется по принципу «как есть» (as is).\n"
    "• Администрация Сервиса не гарантирует бесперебойную и безошибочную работу Сервиса.\n"
    "• Администрация не несёт ответственности за ограничения доступа к сети Интернет, "
    "действия третьих лиц, провайдеров связи либо программного обеспечения пользователя.\n"
    "• Пользователь самостоятельно несёт ответственность за сохранность своих данных доступа.\n\n"

    "7. Конфиденциальность\n"
    "• Обработка персональных данных осуществляется в соответствии с Политикой конфиденциальности.\n"
    "• Сервис принимает разумные меры для защиты пользовательских данных и безопасности соединения.\n"
    "• Платёжные данные пользователей обрабатываются исключительно платёжными системами.\n\n"

    "8. Изменение условий\n"
    "• Администрация Сервиса вправе изменять настоящее Соглашение без предварительного уведомления.\n"
    "• Актуальная версия Соглашения публикуется в официальных ресурсах Сервиса.\n"
    "• Продолжение использования Сервиса после внесения изменений означает согласие "
    "пользователя с новой редакцией Соглашения.\n\n"

    "9. Реквизиты и контакты\n"
    "ИП: Демин М.С.\n"
    "ИНН: 771823226009\n"
    "ОГРНИП: 326774600364921\n"
    "Служба поддержки: @AXMbotsupport"
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


async def send_vpn_config_file(message: Message, config_text: str):
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
    )


async def send_vpn_config_qr(message: Message, config_text: str):
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
    )


async def show_profile(message: Message, telegram_id: int):
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


async def show_myvpn(message: Message, telegram_id: int):
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


async def grant_trial_access(message: Message, telegram_id: int):
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

            await message.answer(
                "Не получилось выдать бесплатный доступ.\n"
                "Попробуй позже."
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
    )


@dp.message(Command("myvpn"))
async def myvpn_handler(message: Message):
    await show_myvpn(
        message=message,
        telegram_id=message.from_user.id,
    )


@dp.message(F.text == "🎁 Попробовать бесплатно 7 дней")
async def trial_access_button_handler(message: Message):
    await grant_trial_access(
        message=message,
        telegram_id=message.from_user.id,
    )


@dp.message(F.text == "👤 Профиль")
async def profile_button_handler(message: Message):
    await show_profile(
        message=message,
        telegram_id=message.from_user.id,
    )


@dp.message(F.text == "🔐 Мой VPN-конфиг")
async def myvpn_button_handler(message: Message):
    await show_myvpn(
        message=message,
        telegram_id=message.from_user.id,
    )


# ДОБАВЛЕНО: обработчик кнопки "Информация"
@dp.callback_query(F.data == "info")
async def info_callback(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        INFO_TEXT,
        reply_markup=info_keyboard,
    )


# ДОБАВЛЕНО: обработчик кнопки "Пользовательское соглашение"
@dp.callback_query(F.data == "user_agreement")
async def user_agreement_callback(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        USER_AGREEMENT_TEXT,
        reply_markup=agreement_keyboard,
    )


# ДОБАВЛЕНО: удаляет сообщение с соглашением при нажатии "Назад"
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
    )


@dp.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery):
    await callback.answer()

    await show_profile(
        message=callback.message,
        telegram_id=callback.from_user.id,
    )


@dp.callback_query(F.data == "my_vpn_config")
async def my_vpn_config_callback(callback: CallbackQuery):
    await callback.answer()

    await show_myvpn(
        message=callback.message,
        telegram_id=callback.from_user.id,
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
