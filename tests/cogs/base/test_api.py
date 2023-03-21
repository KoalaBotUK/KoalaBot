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


'''

GET /activity

'''


async def test_get_activities(api_client):
    resp = await api_client.get('/scheduled-activity?show_all=False')
    assert resp.status == OK
    text = await resp.text()
    assert text == '[]'


async def test_get_activities_bad_param(api_client):
    resp = await api_client.get('/scheduled-activity?invalid_arg=abc')
    assert resp.status == BAD_REQUEST


async def test_get_activities_missing_param(api_client):
    resp = await api_client.get('/scheduled-activity')
    assert resp.status == BAD_REQUEST


'''

PUT /scheduled-activity  

'''

async def test_put_schedule_activity(api_client):
    resp = await api_client.put('/scheduled-activity', json=
        {
            'activity_type': 'playing',
            'message': 'test',
            'url': 'test.com',
            'start_time': '2025-01-01 00:00:00',
            'end_time': '2026-01-01 00:00:00'
        })
    assert resp.status == CREATED
    text = await resp.text()
    assert text == '{"message": "Activity scheduled"}'


async def test_put_schedule_activity_missing_param(api_client):
    resp = await api_client.put('/scheduled-activity', json=
        {
            'activity_type': 'playing',
            'message': 'test',
            'url': 'test.com',
            'start_time': '2025-01-01 00:00:00'
        })
    assert resp.status == BAD_REQUEST
    text = await resp.text()
    assert text == "400: Unsatisfied Arguments: {'end_time'}"


async def test_put_schedule_activity_bad_activity(api_client):
    resp = await api_client.put('/scheduled-activity', json=
        {
            'activity_type': 'invalidActivity',
            'message': 'test',
            'url': 'test.com',
            'start_time': '2025-01-01 00:00:00',
            'end_time': '2026-01-01 00:00:00'
        })
    assert resp.status == UNPROCESSABLE_ENTITY
    assert await resp.text() == '422: Error scheduling activity: Invalid activity type'


async def test_put_schedule_activity_bad_start_time(api_client):
    resp = await api_client.put('/scheduled-activity', json=
        {
            'activity_type': 'playing',
            'message': 'test',
            'url': 'test.com',
            'start_time': 'invalid_time',
            'end_time': '2026-01-01 00:00:00'
        })
    assert resp.status == UNPROCESSABLE_ENTITY
    assert await resp.text() == '422: Error scheduling activity: Bad start / end time'


async def test_put_schedule_activity_bad_end_time(api_client):
    resp = await api_client.put('/scheduled-activity', json=
        {
            'activity_type': 'invalidActivity',
            'message': 'test',
            'url': 'test.com',
            'start_time': '2026-01-01 00:00:00',
            'end_time': 'invalidTime'
        })
    assert resp.status == UNPROCESSABLE_ENTITY
    assert await resp.text() == '422: Error scheduling activity: Bad start / end time'

'''

PUT /activity

'''


async def test_put_set_activity(api_client):
    resp = await api_client.put('/activity', json=
        {
            'activity_type': 'playing',
            'name': 'test',
            'url': 'test.com'
        })
    assert resp.status == CREATED
    text = await resp.text()
    assert text == '{"message": "Activity set"}'
    assert dpytest.verify().activity().matches(discord.Activity(type=discord.ActivityType.playing, name="test", url="test.com"))


async def test_put_set_activity_bad_req(api_client):
    resp = await api_client.put('/activity', json=
        {
            'activity_type': 'invalidActivity',
            'name': 'test',
            'url': 'test.com'
        })
    assert resp.status == UNPROCESSABLE_ENTITY
    assert await resp.text() == '422: Error setting activity: Invalid activity type'


async def test_put_set_activity_missing_param(api_client):
    resp = await api_client.put('/activity', json=
        {
            'activity_type': 'invalidActivity',
            'url': 'test.com'
        })
    assert resp.status == BAD_REQUEST
    assert await resp.text() == "400: Unsatisfied Arguments: {'name'}"


'''

GET /ping  

'''


async def test_get_ping(api_client):
    with mock.patch('discord.client.Client.latency', new_callable=mock.PropertyMock) as mock_last_transaction:
        mock_last_transaction.return_value = 0.42
        resp = await api_client.get('/ping')
        text = await resp.text()
        assert "Pong! 420ms" in text

'''

GET /version 

'''


async def test_get_version(api_client):
    resp = await api_client.get('/version')
    text = await resp.text()
    assert f"version: {koalabot.__version__}" in text

'''

GET /support

'''


async def test_get_support_link(api_client):
    resp = await api_client.get('/support')
    text = await resp.text()
    assert "Join our support server for more help! https://discord.gg/5etEjVd" in text

'''

POST /load-cog

'''

async def test_post_load_cog(api_client):
    resp = await api_client.post('/load-cog', json=
        {
            'extension': 'announce',
            'package': koalabot.COGS_PACKAGE
        })
    assert resp.status == OK
    text = await resp.text()
    assert text == '{"message": "Cog loaded"}'

async def test_post_load_base_cog(api_client):
    resp = await api_client.post('/load-cog', json=
        {
            'extension': 'base',
            'package': koalabot.COGS_PACKAGE
        })
    assert resp.status == OK
    text = await resp.text()
    assert text == '{"message": "Cog loaded"}'

async def test_post_load_cog_bad_req(api_client):
    resp = await api_client.post('/load-cog', json=
        {
            'extension': 'invalidCog',
            'package': koalabot.COGS_PACKAGE
        })
    assert resp.status == UNPROCESSABLE_ENTITY
    assert await resp.text() == '422: Error loading cog: Invalid extension'

async def test_post_load_cog_missing_param(api_client):
    resp = await api_client.post('/load-cog', json=
        {
            'extension': 'invalidCog'
        })
    assert resp.status == BAD_REQUEST
    assert await resp.text() == "400: Unsatisfied Arguments: {'package'}"

async def test_post_load_cog_already_loaded(api_client):
    await api_client.post('/load-cog', json=
        {
            'extension': 'announce',
            'package': koalabot.COGS_PACKAGE
        })
    
    resp = await api_client.post('/load-cog', json=
        {
            'extension': 'announce',
            'package': koalabot.COGS_PACKAGE
        })
    assert resp.status == UNPROCESSABLE_ENTITY
    assert await resp.text() == '422: Error loading cog: Already loaded'

'''

POST /unload-cog

'''

async def test_post_unload_cog(api_client):
    await api_client.post('/load-cog', json=
        {
            'extension': 'announce',
            'package': koalabot.COGS_PACKAGE
        })

    resp = await api_client.post('/unload-cog', json=
        {
            'extension': 'announce',
            'package': koalabot.COGS_PACKAGE
        })
    assert resp.status == OK
    text = await resp.text()
    assert text == '{"message": "Cog unloaded"}'

async def test_post_unload_cog_not_loaded(api_client):
    resp = await api_client.post('/unload-cog', json=
        {
            'extension': 'announce',
            'package': koalabot.COGS_PACKAGE
        })
    assert resp.status == UNPROCESSABLE_ENTITY
    assert await resp.text() == '422: Error unloading cog: Extension not loaded'

async def test_post_unload_cog_missing_param(api_client):
    resp = await api_client.post('/unload-cog', json=
        {
            'extension': 'invalidCog'
        })
    assert resp.status == BAD_REQUEST
    assert await resp.text() == "400: Unsatisfied Arguments: {'package'}"

async def test_post_unload_base_cog(api_client):
    resp = await api_client.post('/unload-cog', json=
        {
            'extension': 'BaseCog',
            'package': koalabot.COGS_PACKAGE
        })
    assert resp.status == UNPROCESSABLE_ENTITY
    text = await resp.text()
    assert text == "422: Error unloading cog: Sorry, you can't unload the base cog"

'''

POST /enable-extension

'''

@mock.patch("koalabot.ENABLED_COGS", ["announce"])
async def test_post_enable_extension(api_client, bot):
    await koalabot.load_all_cogs(bot)
    guild: discord.Guild = dpytest.get_config().guilds[0]
    resp = await api_client.post('/enable-extension', json={
        'guild_id': guild.id,
        'koala_ext': 'Announce'
    })

    assert resp.status == OK
    text = await resp.text()
    assert text == '{"message": "Extension enabled"}'

async def test_post_enable_extension_bad_req(api_client):
    guild: discord.Guild = dpytest.get_config().guilds[0]

    resp = await api_client.post('/enable-extension', json=
        {
            'guild_id': guild.id,
            'koala_ext': 'Invalid Extension'
        })
    assert resp.status == UNPROCESSABLE_ENTITY
    text = await resp.text()
    assert text == "422: Error enabling extension: Invalid extension"

async def test_post_enable_extension_missing_param(api_client):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    resp = await api_client.post('/enable-extension', json=
        {
            'guild_id': guild.id
        })
    assert resp.status == BAD_REQUEST
    text = await resp.text()
    assert text == "400: Unsatisfied Arguments: {'koala_ext'}"

'''

POST /disable-extension

'''

@mock.patch("koalabot.ENABLED_COGS", ['announce'])
async def test_post_disable_extension(api_client, bot):
    await koalabot.load_all_cogs(bot)
    guild: discord.Guild = dpytest.get_config().guilds[0]
    setup = await api_client.post('/enable-extension', json={
        'guild_id': guild.id,
        'koala_ext': 'Announce'
    })
    assert setup.status == OK

    resp = await api_client.post('/disable-extension', json={
        'guild_id': guild.id,
        'koala_ext': 'Announce'
    })
    assert resp.status == OK
    text = await resp.text()
    assert text == '{"message": "Extension disabled"}'

async def test_post_disable_extension_not_enabled(api_client):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    resp = await api_client.post('/disable-extension', json={
        'guild_id': guild.id,
        'koala_ext': 'Announce'
    })
    assert resp.status == UNPROCESSABLE_ENTITY
    text = await resp.text()
    assert text == "422: Error disabling extension: Extension not enabled"

async def test_post_disable_extension_missing_param(api_client):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    resp = await api_client.post('/disable-extension', json={
        'guild_id': guild.id
    })
    assert resp.status == BAD_REQUEST
    text = await resp.text()
    assert text == "400: Unsatisfied Arguments: {'koala_ext'}"

async def test_post_disable_extension_bad_req(api_client):
    guild: discord.Guild = dpytest.get_config().guilds[0]

    resp = await api_client.post('/disable-extension', json=
        {
            'guild_id': guild.id,
            'koala_ext': 'Invalid Extension'
        })
    assert resp.status == UNPROCESSABLE_ENTITY
    text = await resp.text()
    assert text == "422: Error disabling extension: Extension not enabled"


'''

GET /extensions

'''

@mock.patch("koalabot.ENABLED_COGS", ['announce'])
async def test_get_extension(api_client, bot):
    await koalabot.load_all_cogs(bot)
    guild: discord.Guild = dpytest.get_config().guilds[0]
    resp = await api_client.get('/extensions?guild_id={}'.format(guild.id))
    assert resp.status == OK
    text = await resp.text()
    assert text == '["Announce"]'

async def test_get_extension_bad_param(api_client):
    resp = await api_client.get('/extensions?invalid-arg=abc')
    assert resp.status == BAD_REQUEST
    text = await resp.text()
    assert text == "400: Unsatisfied Arguments: {'guild_id'}"

async def test_get_extension_missing_param(api_client):
    resp = await api_client.get('/extensions')
    assert resp.status == BAD_REQUEST
    text = await resp.text()
    assert text == "400: Unsatisfied Arguments: {'guild_id'}"