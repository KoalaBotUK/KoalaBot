#!/usr/bin/env python
"""
Testing KoalaBot IntroCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

import asyncio

# Libs
import discord.ext.test as dpytest
import mock
import pytest
from discord.ext import commands

# Own modules
import KoalaBot
from koala.cogs.intro_cog import db as intro_db
from koala.cogs.intro_cog.db import get_guild_welcome_message
from koala.cogs.intro_cog.utils import DEFAULT_WELCOME_MESSAGE, BASE_LEGAL_MESSAGE, wait_for_message

# Constants
fake_guild_id = 1000
non_existent_guild_id = 9999

# Variables


@pytest.mark.asyncio
async def test_wait_for_message(utils_cog):
    bot = dpytest.get_config().client
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx = utils_cog.get_last_ctx()

    import threading
    t2 = threading.Timer(interval=0.2, function=dpytest.message, args=("y"))
    t2.start()
    fut = wait_for_message(bot, ctx)
    t2.join()
    assert fut, dpytest.sent_queue


@pytest.mark.asyncio
async def test_wait_for_message_timeout(utils_cog):
    bot = dpytest.get_config().client
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx = utils_cog.get_last_ctx()
    with pytest.raises(asyncio.TimeoutError):
        await wait_for_message(bot, ctx, 0.2)


@pytest.mark.asyncio
async def test_send_welcome_message():
    msg_mock = dpytest.back.make_message('y', dpytest.get_config().members[0], dpytest.get_config().channels[0])
    with mock.patch('discord.client.Client.wait_for', mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "send_welcome_message")
    assert dpytest.verify().message().content("This will DM 1 people. Are you sure you wish to do this? Y/N")
    assert dpytest.verify().message().content("Okay, sending out the welcome message now.")
    assert dpytest.verify().message().content(f"{DEFAULT_WELCOME_MESSAGE}\r\n{BASE_LEGAL_MESSAGE}")


@pytest.mark.asyncio
async def test_send_welcome_message_cancelled():
    msg_mock = dpytest.back.make_message('n', dpytest.get_config().members[0], dpytest.get_config().channels[0])
    with mock.patch('discord.client.Client.wait_for', mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "send_welcome_message")
    assert dpytest.verify().message().content("This will DM 1 people. Are you sure you wish to do this? Y/N")
    assert dpytest.verify().message().content("Okay, I won't send out the welcome message then.")
    assert dpytest.verify().message().nothing()


@pytest.mark.asyncio
async def test_send_welcome_message_timeout():
    with mock.patch('discord.client.Client.wait_for', mock.AsyncMock(return_value=None)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "send_welcome_message")
        assert dpytest.verify().message().content("This will DM 1 people. Are you sure you wish to do this? Y/N")
        assert dpytest.verify().message().content('Timed out.')
        assert dpytest.verify().message().content("Okay, I won't send out the welcome message then.")
        assert dpytest.verify().message().nothing()


@pytest.mark.asyncio
async def test_cancel_update_welcome_message():
    guild = dpytest.get_config().guilds[0]
    old_message = get_guild_welcome_message(guild.id)
    new_message = "this is a non default message"
    msg_mock = dpytest.back.make_message('n', dpytest.get_config().members[0], dpytest.get_config().channels[0])
    with mock.patch('discord.client.Client.wait_for', mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + new_message)

    assert dpytest.verify().message().content(f"""Your current welcome message is:\n\r{old_message}""")
    assert dpytest.verify().message().content(
        f"""Your new welcome message will be:\n\r{new_message}\n\r{BASE_LEGAL_MESSAGE}""" +
        """\n\rWould you like to update the message? Y/N?""")
    assert dpytest.verify().message().content("Okay, I won't update the welcome message then.")
    assert dpytest.verify().message().nothing()
    assert intro_db.fetch_guild_welcome_message(guild.id) != new_message


@pytest.mark.asyncio
async def test_update_welcome_message():
    guild = dpytest.get_config().guilds[0]
    old_message = get_guild_welcome_message(guild.id)
    new_message = "this is a non default message"
    msg_mock = dpytest.back.make_message('y', dpytest.get_config().members[0], dpytest.get_config().channels[0])
    with mock.patch('discord.client.Client.wait_for', mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + new_message)

    assert dpytest.verify().message().content(f"""Your current welcome message is:\n\r{old_message}""")
    assert dpytest.verify().message().content(
        f"""Your new welcome message will be:\n\r{new_message}\n\r{BASE_LEGAL_MESSAGE}""" +
        """\n\rWould you like to update the message? Y/N?""")
    assert dpytest.verify().message().content("Okay, updating the welcome message of the guild in the database now.")
    assert dpytest.verify().message().content(
        "Updated in the database, your new welcome message is this is a non default message.")
    assert dpytest.verify().message().nothing()
    assert intro_db.fetch_guild_welcome_message(guild.id) == new_message


@pytest.mark.asyncio
async def test_update_welcome_message_too_long():
    import random, string
    guild = dpytest.get_config().guilds[0]
    old_message = get_guild_welcome_message(guild.id)
    new_message = "".join(random.choice(string.ascii_letters) for _ in range(1800))
    msg_mock = dpytest.back.make_message('y', dpytest.get_config().members[0], dpytest.get_config().channels[0])
    with mock.patch('discord.client.Client.wait_for', mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + new_message)
    assert dpytest.verify().message().content(
        "Your welcome message is too long to send, sorry. The maximum character limit is 1600.")
    assert dpytest.verify().message().nothing()
    assert intro_db.fetch_guild_welcome_message(guild.id) != new_message


@pytest.mark.asyncio
async def test_update_welcome_message_no_args():
    with pytest.raises(commands.MissingRequiredArgument):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message")
    assert dpytest.verify().message().content("Please put in a welcome message to update to.")


@pytest.mark.asyncio
async def test_view_welcome_message():
    guild = dpytest.get_config().guilds[0]
    old_message = get_guild_welcome_message(guild.id)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "welcomeViewMsg ")
    assert dpytest.verify().message().content(f"""Your current welcome message is:\n\r{old_message}""")


@pytest.mark.asyncio
async def test_update_welcome_message_timeout():
    guild = dpytest.get_config().guilds[0]
    old_message = get_guild_welcome_message(guild.id)
    new_message = "this is a non default message"
    # msg_mock = dpytest.back.make_message('y', dpytest.get_config().members[0], dpytest.get_config().channels[0])
    with mock.patch('discord.client.Client.wait_for', mock.AsyncMock(return_value=None)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + new_message)

    assert dpytest.verify().message().content(f"""Your current welcome message is:\n\r{old_message}""")
    assert dpytest.verify().message().content(
        f"""Your new welcome message will be:\n\r{new_message}\n\r{BASE_LEGAL_MESSAGE}""" +
        """\n\rWould you like to update the message? Y/N?""")
    assert dpytest.verify().message().content("Timed out.")
    assert dpytest.verify().message().content("Okay, I won't update the welcome message then.")
    assert dpytest.verify().message().nothing()
    assert intro_db.fetch_guild_welcome_message(guild.id) != new_message
