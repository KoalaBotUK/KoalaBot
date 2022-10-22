from http.client import BAD_REQUEST, CREATED, OK, UNPROCESSABLE_ENTITY

# Libs
import discord
import pytest
from aiohttp import web

import koalabot
from koala.cogs.announce.api import AnnounceEndpoint
from koala.db import get_all_available_guild_extensions
from koala.rest.api import parse_request


@pytest.fixture
def api_client(bot: discord.ext.commands.Bot, aiohttp_client, loop ):
    app = web.Application()
    endpoint = AnnounceEndpoint(bot)
    app = endpoint.register(app)
    return loop.run_until_complete(aiohttp_client(app))

# Check if announce cog is enabled
async def test_is_announce_cog_enabled(api_client):
    resp = await api_client.get('/announce_status?guild=1')
    assert resp.status == OK
    assert await resp.json() == True