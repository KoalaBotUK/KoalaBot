import os

from dotenv import load_dotenv

load_dotenv()

AUTHER_URL = os.environ.get('AUTHER_URL')
AUTHER_CLIENT_ID = os.environ.get('AUTHER_CLIENT_ID')
AUTHER_CLIENT_SECRET = os.environ.get('AUTHER_CLIENT_SECRET')

KB2_URL = os.environ.get('KB2_URL')
