
import asyncio
import os
import signal
import subprocess
import sys

import aiohttp
from aiohttp_socks import ProxyConnector

from settings import (
    BASE_DIR,
    TOR_EXE,
    TORRC,
    PROXY_HOST,
    PROXY_PORT,
    CHECK_INTERVAL,
    FAILURE_LIMIT,
    TOR_LOG,
    TOR_LOG_BACKUP,
    BOT_FILE,
    CHECK_URL,
    MAX_LOG_SIZE,
)


PROJECT_DIR = BASE_DIR

PROXY_URL = f"socks5://{PROXY_HOST}:{PROXY_PORT}"


def prepare_log():
    TOR_LOG_BACKUP.unlink(missing_ok=True)

    if TOR_LOG.exists():
        TOR_LOG.replace(TOR_LOG_BACKUP)


async def save_tor_log(stream):
    size = 0
    log = open(TOR_LOG, "wb")

    try:
        while True:
            line = await stream.readline()

            if not line:
                break

            if size + len(line) > MAX_LOG_SIZE:
                log.close()
                TOR_LOG_BACKUP.unlink(missing_ok=True)

                if TOR_LOG.exists():
                    TOR_LOG.replace(TOR_LOG_BACKUP)

                log = open(TOR_LOG, "wb")
                size = 0

            log.write(line)
            log.flush()
            size += len(line)

    finally:
        log.close()


async def start_tor():
    print("Запускаю Tor...")

    process = await asyncio.create_subprocess_exec(
        str(TOR_EXE),
        "-f",
        str(TORRC),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(TOR_EXE.parent),
    )

    log_task = asyncio.create_task(
        save_tor_log(process.stdout)
    )

    return process, log_task


async def check_connection(use_tor):
    connector = (
        ProxyConnector.from_url(PROXY_URL)
        if use_tor
        else aiohttp.TCPConnector()
    )

    timeout = aiohttp.ClientTimeout(total=8)

    try:
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
        ) as session:
            async with session.get(CHECK_URL) as response:
                return response.status < 500

    except (aiohttp.ClientError, OSError, asyncio.TimeoutError):
        return False


async def wait_for_tor(process):
    for attempt in range(60):
        if process.returncode is not None:
            return False

        if await check_connection(use_tor=True):
            print("\nTor подключён!")
            return True

        print(
            f"\rОжидание Tor: {attempt + 1}/60",
            end="",
            flush=True,
        )

        await asyncio.sleep(3)

    print("\nTor не подключился за 60 попыток.")
    return False


async def stop_process(process, bot=False):
    if process is None or process.returncode is not None:
        return

    try:
        if bot and os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            process.terminate()

        await asyncio.wait_for(process.wait(), timeout=5)

    except (asyncio.TimeoutError, ProcessLookupError):
        if process.returncode is None:
            process.kill()
            await process.wait()


async def restart_tor(process, log_task):
    print("\nПерезапускаю Tor...")

    await stop_process(process)
    await log_task

    while True:
        process, log_task = await start_tor()

        if await wait_for_tor(process):
            return process, log_task

        print("Повторная попытка через 10 секунд...")
        await stop_process(process)
        await log_task
        await asyncio.sleep(10)


async def main():
    for path in (TOR_EXE, TORRC, BOT_FILE):
        if not path.is_file():
            raise FileNotFoundError(f"Файл не найден: {path}")

    tor_process = None
    bot_process = None
    log_task = None

    try:
        prepare_log()

        tor_process, log_task = await start_tor()

        while not await wait_for_tor(tor_process):
            await stop_process(tor_process)
            await log_task
            await asyncio.sleep(10)
            tor_process, log_task = await start_tor()

        print("Запускаю Telegram-бота...")

        bot_process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(BOT_FILE),
            cwd=str(PROJECT_DIR),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )


        print("Бот запущен. Для остановки нажми Ctrl+C.")

        failures = 0
        previous_state = None

        bot_restart_delay = 5
        bot_started_at = asyncio.get_running_loop().time()

        while True:
            # Если сам процесс Tor завершился — восстанавливаем его.
            if tor_process.returncode is not None:
                print("\nПроцесс Tor завершился.")

                tor_process, log_task = await restart_tor(
                    tor_process,
                    log_task,
                )

                failures = 0
                previous_state = None
                continue

            # Если бот завершился — запускаем его заново.
            if bot_process.returncode is not None:
                print(
                    f"\nБот завершился. "
                    f"Перезапуск через {bot_restart_delay} секунд..."
                )

                await asyncio.sleep(bot_restart_delay)

                if tor_process.returncode is not None:
                    continue

                bot_process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    str(BOT_FILE),
                    cwd=str(PROJECT_DIR),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )

                print("Бот запущен повторно.")

                bot_started_at = asyncio.get_running_loop().time()

                bot_restart_delay = min(bot_restart_delay * 2, 300)

                continue

            # Сбрасываем задержку после 10 минут стабильной работы.
            if (
                bot_restart_delay > 5
                and asyncio.get_running_loop().time() - bot_started_at >= 600
            ):
                bot_restart_delay = 5
                print("\nБот стабильно работает. Задержка перезапуска сброшена.")

            # Проверяем обычный интернет и Tor.
            internet_ok = await check_connection(use_tor=False)
            tor_ok = await check_connection(use_tor=True)

            if not internet_ok:
                state = (
                    "Обычный интернет недоступен, но Tor работает"
                    if tor_ok
                    else "Обычный интернет и Tor недоступны"
                )
                failures = 0

            elif not tor_ok:
                state = "Интернет работает, Tor недоступен"
                failures += 1

            else:
                state = "Интернет и Tor работают"
                failures = 0

            if state != previous_state:
                print(f"\n{state}")
                previous_state = state

            print(
                f"Неудачные проверки Tor: "
                f"{failures}/{FAILURE_LIMIT}",
                end="\r",
                flush=True,
            )

            if failures >= FAILURE_LIMIT:
                tor_process, log_task = await restart_tor(
                    tor_process,
                    log_task,
                )

                failures = 0
                previous_state = None

            await asyncio.sleep(CHECK_INTERVAL)

    finally:
        print("\nОстанавливаю процессы...")

        await stop_process(bot_process, bot=True)
        await stop_process(tor_process)

        if log_task is not None:
            await log_task

        print("Работа завершена.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОстановка по Ctrl+C.")
