from http.client import BAD_REQUEST, CREATED, OK, UNPROCESSABLE_ENTITY
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
    resp = await api_client.get('/activity?show_all=False')
    assert resp.status == OK
    text = await resp.text()
    assert text == '[]'

async def test_get_activities_bad_param(api_client):
    resp = await api_client.get('/activity?invalid_arg=abc')
    assert resp.status == BAD_REQUEST

async def test_get_activities_missing_param(api_client):
    resp = await api_client.get('/activity')
    assert resp.status == BAD_REQUEST

'''

POST /scheduleActivity  

'''

async def test_post_schedule_activity(api_client):
    resp = await api_client.post('/scheduleActivity', data=(
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
    resp = await api_client.post('/scheduleActivity', data=(
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
    resp = await api_client.post('/scheduleActivity', data=(
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
    resp = await api_client.post('/scheduleActivity', data=(
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
    resp = await api_client.post('/scheduleActivity', data=(
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

PUT /setActivity

'''

async def test_put_set_activity(api_client):
    resp = await api_client.put('/setActivity', data=(
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
    resp = await api_client.put('/setActivity', data=(
        {
            'activity_type': 'invalidActivity',
            'name': 'test',
            'url': 'test.com'
        }))
    assert resp.status == UNPROCESSABLE_ENTITY
    assert await resp.text() == '422: Error setting activity: Invalid activity type'

async def test_put_set_activity_missing_param(api_client):
    resp = await api_client.put('/setActivity', data=(
        {
            'activity_type': 'invalidActivity',
            'url': 'test.com'
        }))
    assert resp.status == BAD_REQUEST
    assert await resp.text() == "400: Unsatisfied Arguments: {'name'}"