# Futures


# Built-in/Generic Imports


# Libs
from http.client import CREATED, OK, BAD_REQUEST
from aiohttp import web
import discord
from discord.ext.commands import Bot

# Own modules
from . import core
from .log import logger
from koala.rest.api import parse_request, build_response
from koala.utils import convert_iso_datetime

# Constants


# Variables

class VerifyEndpoint:
    """
    THe API endpoints for Verification
    """
    def __init__(self, bot):
        self._bot = bot

    def register(self, app):
        """
        Register the routes for Verify Cog
        todo: review aiohttp 'views' and see if they are a better idea
        :param app: The aiohttp.web.Application (likely of the sub app)
        :return: app
        """
        app.add_routes([])
        return app