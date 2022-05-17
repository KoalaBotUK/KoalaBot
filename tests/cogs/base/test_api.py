from http.client import BAD_REQUEST, CREATED, OK, UNPROCESSABLE_ENTITY

from discord.ext import commands
from mock import mock

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

POST /scheduled-activity  

'''

async def test_post_schedule_activity(api_client):
    resp = await api_client.post('/scheduled-activity', data=(
        {
            'activity_type': 'playing',
            'message': 'test',
            'url': 'test.com',
            'start_time': '2025-01-01 00:00:00',
            'end_time': '2026-01-01 00:00:00'
        }))
    assert resp.status == CREATED
    text = await resp.text()
    assert text == '{"message": "Activity scheduled"}'


async def test_post_schedule_activity_missing_param(api_client):
    resp = await api_client.post('/scheduled-activity', data=(
        {
            'activity_type': 'playing',
            'message': 'test',
            'url': 'test.com',
            'start_time': '2025-01-01 00:00:00'
        }))
    assert resp.status == BAD_REQUEST
    text = await resp.text()
    assert text == "400: Unsatisfied Arguments: {'end_time'}"


async def test_post_schedule_activity_bad_activity(api_client):
    resp = await api_client.post('/scheduled-activity', data=(
        {
            'activity_type': 'invalidActivity',
            'message': 'test',
            'url': 'test.com',
            'start_time': '2025-01-01 00:00:00',
            'end_time': '2026-01-01 00:00:00'
        }))
    assert resp.status == UNPROCESSABLE_ENTITY
    assert await resp.text() == '422: Error scheduling activity: Invalid activity type'


async def test_post_schedule_activity_bad_start_time(api_client):
    resp = await api_client.post('/scheduled-activity', data=(
        {
            'activity_type': 'playing',
            'message': 'test',
            'url': 'test.com',
            'start_time': 'invalid_time',
            'end_time': '2026-01-01 00:00:00'
        }))
    assert resp.status == UNPROCESSABLE_ENTITY
    assert await resp.text() == '422: Error scheduling activity: Bad start / end time'


async def test_post_schedule_activity_bad_end_time(api_client):
    resp = await api_client.post('/scheduled-activity', data=(
        {
            'activity_type': 'invalidActivity',
            'message': 'test',
            'url': 'test.com',
            'start_time': '2026-01-01 00:00:00',
            'end_time': 'invalidTime'
        }))
    assert resp.status == UNPROCESSABLE_ENTITY
    assert await resp.text() == '422: Error scheduling activity: Bad start / end time'

'''

PUT /activity

'''


async def test_put_set_activity(api_client):
    resp = await api_client.put('/activity', data=(
        {
            'activity_type': 'playing',
            'name': 'test',
            'url': 'test.com'
        }))
    assert resp.status == CREATED
    text = await resp.text()
    assert text == '{"message": "Activity set"}'
    assert dpytest.verify().activity().matches(discord.Activity(type=discord.ActivityType.playing, name="test", url="test.com"))


async def test_put_set_activity_bad_req(api_client):
    resp = await api_client.put('/activity', data=(
        {
            'activity_type': 'invalidActivity',
            'name': 'test',
            'url': 'test.com'
        }))
    assert resp.status == UNPROCESSABLE_ENTITY
    assert await resp.text() == '422: Error setting activity: Invalid activity type'


async def test_put_set_activity_missing_param(api_client):
    resp = await api_client.put('/activity', data=(
        {
            'activity_type': 'invalidActivity',
            'url': 'test.com'
        }))
    assert resp.status == BAD_REQUEST
    assert await resp.text() == "400: Unsatisfied Arguments: {'name'}"


'''

GET /ping  

'''


async def test_get_ping(api_client, bot: commands.Bot):
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
