from http.client import OK, BAD_REQUEST, INTERNAL_SERVER_ERROR

# Libs
import discord
import discord.ext.test as dpytest
import pytest
from aiohttp import web

from koala.cogs.verification import core
from koala.cogs.verification.api import VerifyEndpoint, CONFIG_ENDPOINT, REVERIFY_ENDPOINT

TEST_EMAIL = 'verify_test@koalabot.uk'
TEST_EMAIL_DOMAIN = 'koalabot.uk'


@pytest.fixture
def api_client(bot: discord.ext.commands.Bot, aiohttp_client, loop):
    app = web.Application()
    endpoint = VerifyEndpoint(bot)
    app = endpoint.register(app)
    return loop.run_until_complete(aiohttp_client(app))


async def test_get_verify_config_empty(api_client):
    guild_id = dpytest.get_config().guilds[0].id

    resp = await api_client.get('/{}?guild_id={}'.format(CONFIG_ENDPOINT, guild_id))
    assert resp.status == OK
    result: dict = await resp.json()

    expected_result = {
        "guild_id": guild_id,
        "roles": [
        ]
    }

    assert expected_result == result


async def test_get_verify_config(api_client):
    guild_id = dpytest.get_config().guilds[0].id
    role_id = dpytest.get_config().guilds[0].roles[0].id

    await api_client.put('/{}'.format(CONFIG_ENDPOINT), json={
        "guild_id": guild_id,
        "roles": [{
            "email_suffix": TEST_EMAIL_DOMAIN,
            "role_id": role_id
        }]
    })

    resp = await api_client.get('/{}?guild_id={}'.format(CONFIG_ENDPOINT, guild_id))
    assert resp.status == OK
    result: dict = await resp.json()

    expected_result = {
        "guild_id": guild_id,
        "roles": [{
            "email_suffix": TEST_EMAIL_DOMAIN,
            "role_id": role_id
        }]
    }
    assert expected_result == result


async def test_put_verify_config(api_client):
    guild_id = dpytest.get_config().guilds[0].id
    role_id = dpytest.get_config().guilds[0].roles[0].id

    resp = await api_client.get('/{}?guild_id={}'.format(CONFIG_ENDPOINT, guild_id))
    assert (await resp.json())["roles"] == []

    resp = await api_client.put('/{}'.format(CONFIG_ENDPOINT), json={
        "guild_id": guild_id,
        "roles": [{
            "email_suffix": TEST_EMAIL_DOMAIN,
            "role_id": role_id
        }]
    })
    assert resp.status == OK
    result: dict = await resp.json()

    expected_result = {
        "guild_id": guild_id,
        "roles": [{
            "email_suffix": TEST_EMAIL_DOMAIN,
            "role_id": role_id
        }]
    }
    assert expected_result == result

    resp = await api_client.get('/{}?guild_id={}'.format(CONFIG_ENDPOINT, guild_id))
    assert (await resp.json())["roles"] != []


async def test_put_verify_config_clear(api_client):
    guild_id = dpytest.get_config().guilds[0].id
    role_id = dpytest.get_config().guilds[0].roles[0].id

    resp = await api_client.get('/{}?guild_id={}'.format(CONFIG_ENDPOINT, guild_id))
    assert (await resp.json())["roles"] == []

    resp = await api_client.put('/{}'.format(CONFIG_ENDPOINT), json={
        "guild_id": guild_id,
        "roles": [{
            "email_suffix": TEST_EMAIL_DOMAIN,
            "role_id": role_id
        }]
    })
    assert resp.status == OK
    result: dict = await resp.json()

    expected_result = {
        "guild_id": guild_id,
        "roles": [{
            "email_suffix": TEST_EMAIL_DOMAIN,
            "role_id": role_id
        }]
    }
    assert expected_result == result

    resp = await api_client.get('/{}?guild_id={}'.format(CONFIG_ENDPOINT, guild_id))
    assert (await resp.json())["roles"] != []

    resp = await api_client.put('/{}'.format(CONFIG_ENDPOINT), json={
        "guild_id": guild_id,
        "roles": []
    })
    assert resp.status == OK
    result: dict = await resp.json()

    expected_result = {
        "guild_id": guild_id,
        "roles": []
    }
    assert expected_result == result

    resp = await api_client.get('/{}?guild_id={}'.format(CONFIG_ENDPOINT, guild_id))
    assert (await resp.json())["roles"] == []

async def test_put_verify_config_clear(api_client):
    guild_id = dpytest.get_config().guilds[0].id
    role_id = dpytest.get_config().guilds[0].roles[0].id

    resp = await api_client.get('/{}?guild_id={}'.format(CONFIG_ENDPOINT, guild_id))
    assert (await resp.json())["roles"] == []

    resp = await api_client.put('/{}'.format(CONFIG_ENDPOINT), json={
        "guild_id": guild_id,
        "roles": [{
            "email_suffix": TEST_EMAIL_DOMAIN,
            "role_id": role_id
        }]
    })
    assert resp.status == OK
    result: dict = await resp.json()

    expected_result = {
        "guild_id": guild_id,
        "roles": [{
            "email_suffix": TEST_EMAIL_DOMAIN,
            "role_id": role_id
        }]
    }
    assert expected_result == result

    resp = await api_client.get('/{}?guild_id={}'.format(CONFIG_ENDPOINT, guild_id))
    assert (await resp.json())["roles"] != []

    resp = await api_client.put('/{}'.format(CONFIG_ENDPOINT), json={
        "guild_id": guild_id,
        "roles": []
    })
    assert resp.status == OK
    result: dict = await resp.json()

    expected_result = {
        "guild_id": guild_id,
        "roles": []
    }
    assert expected_result == result

    resp = await api_client.get('/{}?guild_id={}'.format(CONFIG_ENDPOINT, guild_id))
    assert (await resp.json())["roles"] == []


async def test_post_reverify_nothing(api_client):
    guild_id = dpytest.get_config().guilds[0].id
    role_id = dpytest.get_config().guilds[0].roles[0].id

    resp = await api_client.post('/{}'.format(REVERIFY_ENDPOINT), json={
        "guild_id": guild_id,
        "role_id": role_id})

    assert resp.status == BAD_REQUEST
    result: dict = await resp.json()
    assert result["error"] == "VerifyException"
    assert result["message"] == "Verification is not enabled for that role"


async def test_post_reverify(api_client):
    guild_id = dpytest.get_config().guilds[0].id
    role_id = dpytest.get_config().guilds[0].roles[0].id

    await api_client.put('/{}'.format(CONFIG_ENDPOINT), json={
        "guild_id": guild_id,
        "roles": [{
            "email_suffix": TEST_EMAIL_DOMAIN,
            "role_id": role_id
        }]
    })

    resp = await api_client.post('/{}'.format(REVERIFY_ENDPOINT), json={
        "guild_id": guild_id,
        "role_id": role_id})

    assert resp.status == OK
    result: dict = await resp.json()
    assert result["role_id"] == role_id
