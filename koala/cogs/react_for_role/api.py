# Futures
# Built-in/Generic Imports
# Libs
from http.client import CREATED, OK, BAD_REQUEST
from aiohttp import web
import discord
from discord.ext import commands
from discord.ext.commands import Bot

# Own modules
from . import core
from .log import logger
from koala.rest.api import parse_request, build_response
from koala.utils import convert_iso_datetime

# Constants
RFR_ENDPOINT = 'rfr'
CREATE = 'create'


class RfrEndpoint:
    _bot: commands.Bot
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
        app.add_routes([web.post('/{}'.format(CREATE), self.post_create_rfr_message)])
        return app

    @parse_request
    async def post_create_rfr_message(self, guild_id: int, channel_id: int,
                                      title: str,  description: str, colour: str):
        """
        Create a React For Role message

        :param guild_id: ID of guild
        :param channel_id: Channel ID of RFR message
        :param title: Title of RFR message
        :param description: Description of RFR message
        :param colour: Hex colour code of RFR message
        :return:
        """
        return {"rfr_id": await core.create_rfr_message(title=title, guild=self._bot.get_guild(guild_id),
                                                        description=description,
                                                        colour=discord.Colour.from_str(colour),
                                                        channel=self._bot.get_channel(channel_id))}


def setup(bot: Bot):
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    sub_app = web.Application()
    endpoint = RfrEndpoint(bot)
    endpoint.register(sub_app)
    getattr(bot, "koala_web_app").add_subapp('/{}'.format(RFR_ENDPOINT), sub_app)
    logger.info("RFR API is ready.")
