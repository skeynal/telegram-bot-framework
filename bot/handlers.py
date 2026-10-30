from aiogram import Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message


# ВРЕМЕННЫЕ ОБРАБОТЧИКИ ДЛЯ ПРОВЕРКИ РАБОТЫ БОТА.
# В дальнейшем их можно заменить или удалить.

def register_handlers(dp: Dispatcher):
    """Регистрирует временные обработчики Telegram-бота."""

    @dp.message(CommandStart())
    async def start_handler(message: Message):
        await message.answer(
            "Привет! Бот работает.\n"
            "Пока это тестовая версия."
        )

    @dp.message(F.text)
    async def echo_handler(message: Message):
        await message.answer(message.text)