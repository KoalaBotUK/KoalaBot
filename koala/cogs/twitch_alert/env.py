import os

from dotenv import load_dotenv

load_dotenv()

TWITCH_KEY = os.environ.get('TWITCH_TOKEN')
TWITCH_SECRET = os.environ.get('TWITCH_SECRET')
