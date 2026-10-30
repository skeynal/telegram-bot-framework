
import os
from pathlib import Path
from dotenv import load_dotenv

# Папка проекта
BASE_DIR = Path(__file__).resolve().parent

# Загружаем настройки из .env
load_dotenv(BASE_DIR / ".env")

# Настройки Tor
TOR_EXE = Path(os.getenv("TOR_EXE", r"C:\tor-bot\tor\tor.exe"))
TORRC = Path(os.getenv("TORRC", r"C:\tor-bot\tor\torrc"))

# Настройки прокси
PROXY_HOST = os.getenv("PROXY_HOST", "127.0.0.1")
PROXY_PORT = int(os.getenv("PROXY_PORT", "9155"))

# Контроль соединения
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "10"))
FAILURE_LIMIT = int(os.getenv("FAILURE_LIMIT", "3"))

# Файлы логов
TOR_LOG = BASE_DIR / "tor.log"
TOR_LOG_BACKUP = BASE_DIR / "tor.log.1"

# Файл бота
BOT_FILE = BASE_DIR / "main.py"

# Дополнительные настройки
CHECK_URL = os.getenv("CHECK_URL", "https://example.com/")
MAX_LOG_SIZE = int(os.getenv("MAX_LOG_SIZE", str(5 * 1024 * 1024)))
