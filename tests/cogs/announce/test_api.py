from http.client import BAD_REQUEST, CREATED, OK, UNPROCESSABLE_ENTITY

from mock import mock
from koala.db import get_all_available_guild_extensions
from koala.rest.api import parse_request

import koalabot
from koala.cogs.base.api import BaseEndpoint

# Libs
import discord
from aiohttp import web
import pytest
import discord.ext.test as dpytest


@pytest.fixture
def api_client(bot: discord.ext.commands.Bot, aiohttp_client, loop ):
    app = web.Application()
    endpoint = BaseEndpoint(bot)
    app = endpoint.register(app)
    return loop.run_until_complete(aiohttp_client(app))