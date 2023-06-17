from http.client import BAD_REQUEST, CREATED, OK, UNPROCESSABLE_ENTITY, NOT_FOUND

# Libs
import discord
import discord.ext.test as dpytest
import pytest
from aiohttp import web

from koala.cogs.voting.api import VotingEndpoint

# Variables
options = [["option1", "body1"],
            ["option2", "body2"]]

@pytest.fixture
def api_client(bot: discord.ext.commands.Bot, aiohttp_client, loop):
    app = web.Application()
    endpoint = VotingEndpoint(bot)
    app = endpoint.register(app)
    return loop.run_until_complete(aiohttp_client(app))


# POST /config
# not sure how to test for any error handling

async def test_post_new_vote_no_optionals(api_client):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    resp = await api_client.post('/config', json=
    {
        'title': 'Test',
        'author_id': author.id,
        'guild_id': guild.id,
        'options': options
    })
    
    assert resp.status == CREATED
    assert (await resp.json())['message'] == "Vote Test created"


async def test_post_new_vote_with_optionals(api_client):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    resp = await api_client.post('/config', json=
    {
        'title': 'Test2',
        'author_id': author.id,
        'guild_id': guild.id,
        'options': options,
        'roles': [guild.roles[0].id],
        'chair_id': guild.members[1].id,
        'end_time': '2025-01-01 00:00:00'
    })
    
    assert resp.status == CREATED
    assert (await resp.json())['message'] == "Vote Test2 created"


# GET /config

async def test_get_current_votes(api_client):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    await api_client.post('/config', json=
    {
        'title': 'Test',
        'author_id': author.id,
        'guild_id': guild.id,
        'options': options
    })

    resp = await api_client.get('/config?author_id={}&guild_id={}'.format(author.id, guild.id))
    assert resp.status == OK
    
    jresp = await resp.json()
    
    assert jresp['embed_title'] == "Your current votes"
    assert jresp['embed_body'] == "Test\n"


async def test_get_current_votes_no_votes(api_client):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    resp = await api_client.get('/config?author_id={}&guild_id={}'.format(author.id, guild.id))
    assert resp.status == OK
    
    jresp = await resp.json()
    
    assert jresp['embed_title'] == "Your current votes"
    assert jresp['embed_body'] == "No current votes"


# POST /results
async def test_post_results(api_client):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    await api_client.post('/config', json=
    {
        'title': 'Test',
        'author_id': author.id,
        'guild_id': guild.id,
        'options': options
    })

    resp = await api_client.post('/results', json={
        'author_id': author.id,
        'title': 'Test'
    })

    assert resp.status == OK
    jresp = await resp.json()

    assert jresp['embed_title'] == "Test Results:"
    assert jresp['embed_body'] == "option1, 1 votes\noption2, 0 votes\n"
    # how the hell is this getting votes?

    resp = await api_client.get('/config?author_id={}&guild_id={}'.format(author.id, guild.id))
    
    assert (await resp.json())['embed_body'] == "No current votes"


# GET /results
async def test_get_results(api_client):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    author: discord.Member = guild.members[0]

    resp2 = await api_client.post('/config', json=
    {
        'title': 'Test2',
        'author_id': author.id,
        'guild_id': guild.id,
        'options': options
    })

    assert resp2.status == CREATED
    assert (await resp2.json())['message'] == "Vote Test2 created"

    # for SOME REASON it thinks its an invalid vote; the post is fine

    resp = await api_client.get('/results?author_id={}&title=Test2'.format(author.id))
    assert resp.status == OK
    jresp = await resp.json()

    assert jresp['embed_title'] == "Test2 Results:"
    assert jresp['embed_body'] == "option1, 1 votes\noption2, 0 votes\n"

    # checking vote hasn't closed
    resp = await api_client.get('/config?author_id={}&guild_id={}'.format(author.id, guild.id))
    
    assert (await resp.json())['embed_body'] == "Test2\n"
    