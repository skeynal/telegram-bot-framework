from aiogram.client.session.aiohttp import AiohttpSession
from settings import PROXY_HOST, PROXY_PORT

PROXY_URL = f"socks5://{PROXY_HOST}:{PROXY_PORT}"


def create_session() -> AiohttpSession:
    return AiohttpSession(proxy=PROXY_URL)