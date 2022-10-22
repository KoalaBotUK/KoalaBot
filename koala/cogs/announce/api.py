# Futures
# Built-in/Generic Imports
# Libs
from http.client import BAD_REQUEST, CREATED, OK

import discord
from aiohttp import web
from discord.ext.commands import Bot

from koala.rest.api import build_response, parse_request
from koala.utils import convert_iso_datetime

# Own modules
from . import cog
from .log import logger

# Constants
ANNOUNCE_ENDPOINT = 'announce'

ANNOUNCE_STATUS= 'announce_status' # GET


class AnnounceEndpoint:
    """
    The API endpoints for AnnounceCog
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
        app.add_routes([web.get('/{endpoint}'.format(endpoint=ANNOUNCE_STATUS), self.get_announce_is_enabled)])
        return app


    @parse_request
    async def get_announce_is_enabled(guild):
        return await cog.announce_is_enabled(guild)


def setup(bot: Bot):
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    sub_app = web.Application()
    endpoint = AnnounceEndpoint(bot)
    endpoint.register(sub_app)
    getattr(bot, "koala_web_app").add_subapp('/{extension}'.format(extension=ANNOUNCE_ENDPOINT), sub_app)
    logger.info("Announce API is ready.")
