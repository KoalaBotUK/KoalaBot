import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ['DISCORD_TOKEN']
BOT_OWNER = os.environ.get('BOT_OWNER')

DB_KEY = os.environ.get('SQLITE_KEY', "2DD29CA851E7B56E4697B0E1F08507293D761A05CE4D1B628663F411A8086D99")
ENCRYPTED_DB = (not os.name == 'nt') and eval(os.environ.get('ENCRYPTED', "True"))

CONFIG_PATH = os.environ.get("CONFIG_PATH", "./config")
LOGGING_FILE = eval(os.environ.get("LOGGING_FILE", "True"))