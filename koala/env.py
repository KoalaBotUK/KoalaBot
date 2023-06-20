import os
from pathlib import Path

from dotenv import load_dotenv

from .enums import DatabaseType

load_dotenv()

BOT_TOKEN = os.environ['DISCORD_TOKEN']
BOT_OWNER_ENV = os.environ.get('BOT_OWNER')
BOT_OWNER_STR = BOT_OWNER_ENV.split(',')
BOT_OWNER = [int(item) for item in BOT_OWNER_STR]

API_PORT = os.environ.get("API_PORT", 8080)

# Logging
LOGGING_FILE = eval(os.environ.get("LOGGING_FILE", "True"))

# CORS
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# Config Path
CONFIG_PATH = os.environ.get("CONFIG_PATH")

if not CONFIG_PATH:
    CONFIG_PATH = "/config"
    if os.name == 'nt':
        CONFIG_PATH = '.'+CONFIG_PATH
CONFIG_PATH = Path(CONFIG_PATH)
CONFIG_PATH.mkdir(exist_ok=True, parents=True)

# Database
DB_URL = os.environ.get("DB_URL")
DB_TYPE = DatabaseType[os.environ.get("DB_TYPE", "MYSQL")]

if not DB_URL or DB_TYPE == DatabaseType.SQLITE:
    # Use SQLite
    DB_TYPE = DatabaseType["SQLITE"]
    ENCRYPTED_DB = (not os.name == 'nt') and eval(os.environ.get('ENCRYPTED', "True"))
    DB_KEY = os.environ.get('SQLITE_KEY', "2DD29CA851E7B56E4697B0E1F08507293D761A05CE4D1B628663F411A8086D99")
    SQLITE_DB_PATH = Path(CONFIG_PATH, "Koala.db" if ENCRYPTED_DB else "windows_Koala.db")
    SQLITE_DB_PATH.touch()
    if ENCRYPTED_DB:
        os.system(f"chown www-data {CONFIG_PATH.absolute()}")
        os.system(f"chmod 777 {CONFIG_PATH}")
        DB_URL = f"sqlite+pysqlcipher://:x'{DB_KEY}'@/{SQLITE_DB_PATH.absolute()}?charset=utf8mb4"
    else:
        DB_URL = f"sqlite:///{SQLITE_DB_PATH.absolute()}?charset=utf8mb4"
