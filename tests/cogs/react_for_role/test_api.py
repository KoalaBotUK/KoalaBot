from http.client import OK

# Libs
import discord
import discord.ext.test as dpytest
import mock
import pytest
from aiohttp import web

from koala.cogs.react_for_role.api import RfrEndpoint, MESSAGE, REQUIRED_ROLES


@pytest.fixture
def api_client(bot: discord.ext.commands.Bot, aiohttp_client, loop):
    app = web.Application()
    endpoint = RfrEndpoint(bot)
    app = endpoint.register(app)
    return loop.run_until_complete(aiohttp_client(app))


@mock.patch('koala.cogs.react_for_role.core.overwrite_channel_add_reaction_perms', mock.AsyncMock())
async def test_message_post_partial(api_client):
    resp = await api_client.post('/{}'.format(MESSAGE), json={
        "guild_id": dpytest.get_config().guilds[0].id,
        "channel_id": dpytest.get_config().guilds[0].channels[0].id,
        "title": "API test",
        "description": "desc",
        "colour": "#0000ff"
    })
    assert resp.status == OK
    resp_json: dict = await resp.json()
    assert "message_id" in resp_json.keys()


@mock.patch('koala.cogs.react_for_role.core.overwrite_channel_add_reaction_perms', mock.AsyncMock())
async def test_message_post_full(api_client):
    resp = await api_client.post('/{}'.format(MESSAGE), json={
        "guild_id": dpytest.get_config().guilds[0].id,
        "channel_id": dpytest.get_config().guilds[0].channels[0].id,
        "title": "API test",
        "description": "desc",
        "colour": "#0000ff",
        "thumbnail": "https://koalabot.uk/static/media/KoalaBotLogo-min.78f6a0d317dfdfa7391d.png",
        "inline": "true",
        "roles": [{
            "role_id": dpytest.get_config().guilds[0].roles[0].id,
            "emoji": "<:discordmod:1030226250884722809>"
        }]
    })
    assert resp.status == OK
    resp_json: dict = await resp.json()
    assert "message_id" in resp_json.keys()


@mock.patch('koala.cogs.react_for_role.core.overwrite_channel_add_reaction_perms', mock.AsyncMock())
async def test_message_get(api_client):
    resp1 = await api_client.post('/{}'.format(MESSAGE), json={
        "guild_id": dpytest.get_config().guilds[0].id,
        "channel_id": dpytest.get_config().guilds[0].channels[0].id,
        "title": "API test",
        "description": "desc",
        "colour": "#0000ff"
    })
    message_id = (await resp1.json())["message_id"]

    resp = await api_client.get('/{}?message_id={}&guild_id={}&channel_id={}'
                                .format(MESSAGE,
                                        message_id,
                                        dpytest.get_config().guilds[0].id,
                                        dpytest.get_config().guilds[0].channels[0].id))

    assert resp.status == OK
    resp_json: dict = await resp.json()
    assert resp_json.get("colour") == "#0000ff"


@mock.patch('koala.cogs.react_for_role.core.overwrite_channel_add_reaction_perms', mock.AsyncMock())
async def test_message_put(api_client):
    resp1 = await api_client.post('/{}'.format(MESSAGE), json={
        "guild_id": dpytest.get_config().guilds[0].id,
        "channel_id": dpytest.get_config().guilds[0].channels[0].id,
        "title": "API test",
        "description": "desc",
        "colour": "#0000ff"
    })
    post_response = await resp1.json()
    post_response["colour"] = "#ffffff"
    post_response["title"] = "test2"
    post_response["description"] = "desc2"
    assert post_response["thumbnail"] == "https://cdn.discordapp.com/attachments/737280260541907015/752024535985029240/discord1.png"
    post_response["thumbnail"] = "https://koalabot.uk/static/media/KoalaBotLogo-min.78f6a0d317dfdfa7391d.png"
    assert post_response["inline"] is False
    post_response["inline"] = True
    assert post_response["roles"] == []
    post_response["roles"] = [{
        "role_id": dpytest.get_config().guilds[0].roles[0].id,
        "emoji": "<:discordmod:1030226250884722809>"
    }]
    resp = await api_client.put('/{}'.format(MESSAGE), json=post_response)

    assert resp.status == OK
    resp_json: dict = await resp.json()
    assert resp_json.get("colour") == "#ffffff"
    assert resp_json.get("title") == "test2"
    assert resp_json.get("description") == "desc2"
    assert resp_json["thumbnail"] == "https://koalabot.uk/static/media/KoalaBotLogo-min.78f6a0d317dfdfa7391d.png"
    assert resp_json["inline"] is True
    assert resp_json["roles"] == [{
        "role_id": dpytest.get_config().guilds[0].roles[0].id,
        "emoji": "<:discordmod:1030226250884722809>"
    }]


@mock.patch('koala.cogs.react_for_role.core.overwrite_channel_add_reaction_perms', mock.AsyncMock())
async def test_message_patch_partial(api_client):
    resp1 = await api_client.post('/{}'.format(MESSAGE), json={
        "guild_id": dpytest.get_config().guilds[0].id,
        "channel_id": dpytest.get_config().guilds[0].channels[0].id,
        "title": "API test",
        "description": "desc",
        "colour": "#0000ff"
    })
    post_response = await resp1.json()

    patch_body = {
        "message_id": post_response["message_id"],
        "guild_id": dpytest.get_config().guilds[0].id,
        "channel_id": dpytest.get_config().guilds[0].channels[0].id,
        "description": "desc2"
                 }
    resp = await api_client.patch('/{}'.format(MESSAGE), json=patch_body)

    assert resp.status == OK
    message = await dpytest.get_config().guilds[0].channels[0].fetch_message(post_response["message_id"])
    assert message.embeds[0].description == "desc2"
    resp_json: dict = await resp.json()
    assert resp_json.get("colour") == "#0000ff"
    assert resp_json.get("description") == "desc2"


@mock.patch('koala.cogs.react_for_role.core.overwrite_channel_add_reaction_perms', mock.AsyncMock())
async def test_message_patch_full(api_client):
    resp1 = await api_client.post('/{}'.format(MESSAGE), json={
        "guild_id": dpytest.get_config().guilds[0].id,
        "channel_id": dpytest.get_config().guilds[0].channels[0].id,
        "title": "API test",
        "description": "desc",
        "colour": "#0000ff"
    })
    post_response = await resp1.json()

    patch_body = {
        "message_id": post_response["message_id"],
        "guild_id": dpytest.get_config().guilds[0].id,
        "channel_id": dpytest.get_config().guilds[0].channels[0].id,
        "title": "test2",
        "description": "desc2",
        "colour": "#000fff",
        "thumbnail": "https://koalabot.uk/static/media/KoalaBotLogo-min.78f6a0d317dfdfa7391d.png",
        "inline": "true",
        "roles": [{
            "role_id": dpytest.get_config().guilds[0].roles[0].id,
            "emoji": "<:discordmod:1030226250884722809>"
        }]
    }
    resp = await api_client.patch('/{}'.format(MESSAGE), json=patch_body)

    assert resp.status == OK
    message = await dpytest.get_config().guilds[0].channels[0].fetch_message(post_response["message_id"])
    assert message.embeds[0].description == "desc2"
    resp_json: dict = await resp.json()
    assert resp_json.get("colour") == "#000fff"
    assert resp_json.get("title") == "test2"
    assert resp_json.get("description") == "desc2"
    assert resp_json["thumbnail"] == "https://koalabot.uk/static/media/KoalaBotLogo-min.78f6a0d317dfdfa7391d.png"
    assert resp_json["inline"] is True
    assert resp_json["roles"] == [{
        "role_id": dpytest.get_config().guilds[0].roles[0].id,
        "emoji": "<:discordmod:1030226250884722809>"
    }]


@mock.patch('koala.cogs.react_for_role.core.overwrite_channel_add_reaction_perms', mock.AsyncMock())
async def test_message_delete(api_client):
    resp1 = await api_client.post('/{}'.format(MESSAGE), json={
        "guild_id": dpytest.get_config().guilds[0].id,
        "channel_id": dpytest.get_config().guilds[0].channels[0].id,
        "title": "API test",
        "description": "desc",
        "colour": "#0000ff"
    })
    post_response = await resp1.json()

    message = await dpytest.get_config().guilds[0].channels[0].fetch_message(post_response["message_id"])
    assert message is not None
    assert message.embeds[0].description == "desc"

    delete_body = {
        "message_id": post_response["message_id"],
        "guild_id": dpytest.get_config().guilds[0].id,
        "channel_id": dpytest.get_config().guilds[0].channels[0].id
    }
    resp = await api_client.delete('/{}'.format(MESSAGE), json=delete_body)

    assert resp.status == OK
    with pytest.raises(discord.NotFound):
        await dpytest.get_config().guilds[0].channels[0].fetch_message(post_response["message_id"])
    resp_json: dict = await resp.json()
    assert resp_json.get("status") == "DELETED"
    assert resp_json.get("message_id") == post_response["message_id"]


# /REQUIRED_ROLES

async def test_required_roles_put(api_client):
    resp = await api_client.put('/{}'.format(REQUIRED_ROLES), json={
        "guild_id": dpytest.get_config().guilds[0].id,
        "role_ids": [dpytest.get_config().guilds[0].roles[0].id]
    })
    assert resp.status == OK
    resp_json: dict = await resp.json()
    assert resp_json.get("role_ids") == [dpytest.get_config().guilds[0].roles[0].id]
    assert resp_json.get("guild_id") == dpytest.get_config().guilds[0].id


async def test_required_roles_get(api_client):
    await api_client.put('/{}'.format(REQUIRED_ROLES), json={
        "guild_id": dpytest.get_config().guilds[0].id,
        "role_ids": [dpytest.get_config().guilds[0].roles[0].id]
    })

    resp = await api_client.get('/{}?guild_id={}'.format(REQUIRED_ROLES, dpytest.get_config().guilds[0].id))

    assert resp.status == OK
    resp_json: dict = await resp.json()
    assert resp_json.get("role_ids") == [dpytest.get_config().guilds[0].roles[0].id]
    assert resp_json.get("guild_id") == dpytest.get_config().guilds[0].id
