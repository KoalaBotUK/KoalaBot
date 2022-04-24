# Futures
# Built-in/Generic Imports
# Libs
from aiohttp import web
import discord
from discord.ext.commands import Bot

# Own modules
from . import core
from .log import logger
from koala.rest.api import parse_request

# Constants
BASE_ENDPOINT = 'base'
ACTIVITY_ENDPOINT = 'activity'
SET_ACTIVITY_ENDPOINT = 'set-activity'

# Variables


class BaseEndpoint:
    """
    The API endpoints for BaseCog
    """
    def __init__(self, bot):
        self._bot = bot

    def register(self, app):
        """
        Register the routes for the given application
        todo: review aiohttp 'views' and see if they are a better idea
        :param app: The aiohttp.web.Application (likely of the sub app)
        :return: app
        """
        app.add_routes([web.get('/{endpoint}'.format(endpoint=ACTIVITY_ENDPOINT), self.get_activities),
                        web.put('/{endpoint}'.format(endpoint=SET_ACTIVITY_ENDPOINT), self.put_set_activity)])
        return app

    @parse_request
    async def get_activities(self, show_all: bool):
        """
        Get all the scheduled activities
        :param show_all: If you wish to see a time restricted version or not
        :return: The list of ScheduledActivities
        """
        return core.activity_list(show_all=show_all)

    @parse_request
    async def put_set_activity(self, activity_type, name, url):
        """
        Put a given activity as the discord bot's activity
        :param activity_type: activity type (playing, watching, streaming, ...)
        :param name: The content of the activity
        :param url: The url to use (for streaming)
        :return:
        """
        activity_type = discord.ActivityType[activity_type]
        await core.activity_set(activity_type, name, url, self._bot)
        return "Successfully set activity"


def setup(bot: Bot):
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    sub_app = web.Application()
    endpoint = BaseEndpoint(bot)
    endpoint.register(sub_app)
    getattr(bot, "koala_web_app").add_subapp('/{extension}'.format(extension=BASE_ENDPOINT), sub_app)
    logger.info("Base API is ready.")
