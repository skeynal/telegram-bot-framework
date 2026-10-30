
import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from proxy import create_session
from functional import register_handlers, monitor_telegram


dp = Dispatcher()
register_handlers(dp)


async def main():
    session = create_session()

    async with Bot(
        token=BOT_TOKEN,
        session=session,
    ) as bot:
        monitor_task = asyncio.create_task(
            monitor_telegram(bot, dp)
        )

        try:
            await dp.start_polling(bot)

        finally:
            monitor_task.cancel()

            try:
                await monitor_task
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
