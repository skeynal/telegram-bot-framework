
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message


def register_handlers(dp: Dispatcher):
    """Регистрирует обработчики Telegram-бота."""

    @dp.message(CommandStart())
    async def start_handler(message: Message):
        await message.answer(
            "Привет! Бот работает.\n"
            "Пока это тестовая версия."
        )

    @dp.message(F.text)
    async def echo_handler(message: Message):
        await message.answer(message.text)


async def monitor_telegram(
    bot: Bot,
    dp: Dispatcher,
    interval: int = 30,
    failure_limit: int = 3,
):
    """Проверяет доступность Telegram Bot API."""

    failures = 0

    while True:
        await asyncio.sleep(interval)

        try:
            await bot.get_me()

            if failures:
                print("\nСвязь с Telegram восстановлена.")

            failures = 0

        except asyncio.CancelledError:
            raise

        except Exception as error:
            failures += 1

            print(
                f"\nПроверка Telegram: "
                f"{failures}/{failure_limit} "
                f"— {type(error).__name__}"
            )

            if failures >= failure_limit:
                print(
                    "\nTelegram недоступен. "
                    "Останавливаю polling для перезапуска."
                )

                await dp.stop_polling()
                return
