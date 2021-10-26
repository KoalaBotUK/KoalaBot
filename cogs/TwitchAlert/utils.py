# Futures

# Built-in/Generic Imports
import os

# Own modules
# Libs
import discord
from dotenv import load_dotenv
from utils.KoalaColours import KOALA_GREEN

# Constants
load_dotenv()
DEFAULT_MESSAGE = ""
TWITCH_ICON = "https://cdn3.iconfinder.com/data/icons/social-messaging-ui-color-shapes-2-free" \
              "/128/social-twitch-circle-512.png"
TWITCH_KEY = os.environ.get('TWITCH_TOKEN')
TWITCH_SECRET = os.environ.get('TWITCH_SECRET')

TWITCH_USERNAME_REGEX = "^[a-z0-9][a-z0-9_]{3,24}$"

LOOP_CHECK_LIVE_DELAY = 1
TEAMS_LOOP_CHECK_LIVE_DELAY = 1
REFRESH_TEAMS_DELAY = 5

# Variables


def create_live_embed(stream_info, user_info, game_info, message):
    """
    Creates an embed for the go live announcement
    :param stream_info: The stream data from the Twitch API
    :param user_info: The user data for this streamer from the Twitch API
    :param game_info: The game data for this game from the Twitch API
    :param message: The custom message to be added as a description
    :return: The embed created
    """
    embed = discord.Embed(colour=KOALA_GREEN)
    if message is not None and message != "":
        embed.description = message

    embed.set_author(name=stream_info.get("user_name") + " is now streaming!",
                     icon_url=TWITCH_ICON)
    embed.title = "https://twitch.tv/" + str.lower(stream_info.get("user_login"))

    embed.add_field(name="Stream Title", value=stream_info.get("title"))
    if game_info is None:
        embed.add_field(name="Playing", value="No Category")
    else:
        embed.add_field(name="Playing", value=game_info.get("name"))
    embed.set_thumbnail(url=user_info.get("profile_image_url"))

    return embed


def split_to_100s(array: list):
    if not array:
        return array
    result = []
    while len(array) >= 100:
        result.append(array[:100])
        array = array[100:]
    result.append(array)
    return result
