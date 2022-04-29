import os
from dotenv import load_dotenv
from pathlib import Path

from .enums import DatabaseType

load_dotenv()

BOT_TOKEN = os.environ['DISCORD_TOKEN']
BOT_OWNER = os.environ.get('BOT_OWNER')

# Logging
LOGGING_FILE = eval(os.environ.get("LOGGING_FILE", "True"))

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
