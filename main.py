import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Check your .env file.")


dp = Dispatcher()


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Получить VPN",
                    callback_data="get_vpn",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Помощь",
                    callback_data="help",
                )
            ],
        ]
    )


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Привет! Я помогу получить VPN-конфигурацию.\n\n"
        "Нажмите кнопку ниже:",
        reply_markup=main_keyboard(),
    )


@dp.callback_query(F.data == "get_vpn")
async def get_vpn_handler(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Скоро здесь будет автоматическая выдача WireGuard-конфига."
    )


@dp.callback_query(F.data == "help")
async def help_handler(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Здесь будет инструкция по подключению VPN."
    )


async def main():
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())