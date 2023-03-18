from http.client import BAD_REQUEST, CREATED, OK, UNPROCESSABLE_ENTITY


from mock import mock
from koala.db import get_all_available_guild_extensions
from koala.rest.api import parse_request

import koalabot
from koala.cogs.react_for_role.api import RfrEndpoint

# Libs
import discord
from aiohttp import web
import pytest
import discord.ext.test as dpytest


@pytest.fixture
def api_client(bot: discord.ext.commands.Bot, aiohttp_client, loop ):
    app = web.Application()
    endpoint = RfrEndpoint(bot)
    app = endpoint.register(app)
    return loop.run_until_complete(aiohttp_client(app))

async def test_create_rfr(api_client):
    resp = await api_client.post('/create', json={
    "guild_id": dpytest.get_config().guilds[0].id,
    "channel_id": dpytest.get_config().guilds[0].channels[0].id,
    "title": "API test",
    "description": "desc",
    "colour": "#0000ff"
})
    assert resp.status == OK
    resp_json: dict = await resp.json()
    assert "rfr_id" in resp_json.keys()
