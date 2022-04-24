import discord
from aiohttp import web
from discord.ext.commands import Bot

from . import core
from .log import logger
from koala.rest.api import parse_request

BASE_ENDPOINT = 'base'
ACTIVITY_ENDPOINT = 'activity'
SET_ACTIVITY_ENDPOINT = 'set-activity'


class BaseEndpoint:
    def __init__(self, bot):
        self._bot = bot

    def register(self, app):
        app.add_routes([web.get('/{endpoint}'.format(endpoint=ACTIVITY_ENDPOINT), self.get_activities),
                        web.put('/{endpoint}'.format(endpoint=SET_ACTIVITY_ENDPOINT), self.put_set_activity)])
        return app

    @parse_request
    async def get_activities(self, show_all: bool):
        return core.activity_list(show_all=show_all)

    @parse_request
    async def put_set_activity(self, activity_type, name, url):
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
