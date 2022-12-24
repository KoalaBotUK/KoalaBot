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
import koalabot
from koala.cogs import IntroCog
from koala.cogs.intro_cog import core
from koala.cogs.intro_cog.utils import DEFAULT_WELCOME_MESSAGE, BASE_LEGAL_MESSAGE, wait_for_message
from tests.tests_utils.last_ctx_cog import LastCtxCog
from tests.tests_utils.utils import MockInteraction

# Constants
fake_guild_id = 1000
non_existent_guild_id = 9999

# Variables


@pytest.mark.asyncio
async def test_wait_for_message(utils_cog: LastCtxCog):
    bot = dpytest.get_config().client
    await dpytest.message(koalabot.COMMAND_PREFIX + "store_ctx")
    ctx = utils_cog.get_last_ctx()

    import threading
    t2 = threading.Timer(interval=0.2, function=dpytest.message, args="y")
    t2.start()
    fut = wait_for_message(bot, ctx)
    t2.join()
    assert fut, dpytest.sent_queue


@pytest.mark.asyncio
async def test_wait_for_message_timeout(utils_cog: LastCtxCog):
    bot = dpytest.get_config().client
    await dpytest.message(koalabot.COMMAND_PREFIX + "store_ctx")
    ctx = utils_cog.get_last_ctx()
    with pytest.raises(asyncio.TimeoutError):
        await wait_for_message(bot, ctx, 0.2)


@pytest.mark.asyncio
async def test_send_welcome_message(intro_cog: IntroCog, mock_interaction: MockInteraction):
    async def assert_confirm():
        mock_interaction.response.assert_eq("This will DM 1 people. Are you sure you wish to do this?", partial=True)
        confirm_view = mock_interaction.response.sent_message['view']
        await confirm_view.confirm.callback(mock_interaction)

    with mock.patch('koala.ui.Confirm.wait', mock.AsyncMock(side_effect=assert_confirm)):
        await intro_cog.send_welcome_message.callback(intro_cog, mock_interaction)

    mock_interaction.response.assert_eq("Okay, sending out the welcome message now.", view=None)
    assert dpytest.verify().message().content(f"{DEFAULT_WELCOME_MESSAGE}\n\r{BASE_LEGAL_MESSAGE}")


@pytest.mark.asyncio
async def test_send_welcome_message_cancelled(intro_cog: IntroCog, mock_interaction: MockInteraction):
    async def assert_cancel():
        mock_interaction.response.assert_eq("This will DM 1 people. Are you sure you wish to do this?", partial=True)
        confirm_view = mock_interaction.response.sent_message['view']
        await confirm_view.cancel.callback(mock_interaction)

    with mock.patch('koala.ui.Confirm.wait', mock.AsyncMock(side_effect=assert_cancel)):
        await intro_cog.send_welcome_message.callback(intro_cog, mock_interaction)
    mock_interaction.response.assert_eq("Okay, I won't send out the welcome message then.", view=None)
    assert dpytest.verify().message().nothing()


@pytest.mark.asyncio
async def test_send_welcome_message_timeout(intro_cog: IntroCog, mock_interaction: MockInteraction):
    async def assert_timeout():
        mock_interaction.response.assert_eq("This will DM 1 people. Are you sure you wish to do this?", partial=True)
        confirm_view = mock_interaction.response.sent_message['view']
        confirm_view.timeout = 0

    with mock.patch('koala.ui.Confirm.wait', mock.AsyncMock(side_effect=assert_timeout)):
        await intro_cog.send_welcome_message.callback(intro_cog, mock_interaction)
    mock_interaction.response.assert_eq("Timed out. No message sent.", view=None)
    assert dpytest.verify().message().nothing()


@pytest.mark.asyncio
async def test_cancel_update_welcome_message(intro_cog: IntroCog, mock_interaction: MockInteraction):
    guild_id = dpytest.get_config().guilds[0].id
    old_message = core.get_guild_welcome_message(guild_id)
    new_message = "this is a non default message"

    await intro_cog.edit_welcome_message.callback(intro_cog, mock_interaction)
    modal = mock_interaction.response.sent_modal
    assert modal.message.default == DEFAULT_WELCOME_MESSAGE
    modal.message._value = new_message
    assert not mock_interaction.response.sent_message

    assert core.fetch_guild_welcome_message(guild_id) != new_message


@pytest.mark.asyncio
async def test_update_welcome_message(intro_cog: IntroCog, mock_interaction: MockInteraction):
    new_message = "this is a non default message"
    core.new_guild_welcome_message(mock_interaction.guild_id)
    await intro_cog.edit_welcome_message.callback(intro_cog, mock_interaction)
    modal = mock_interaction.response.sent_modal
    assert modal.message.default == DEFAULT_WELCOME_MESSAGE
    modal.message._value = new_message
    await modal.on_submit(mock_interaction)
    mock_interaction.response.assert_eq(f'Thanks for your response we have updated the welcome message to:'
                                        f'\n\r{new_message}\n\r{BASE_LEGAL_MESSAGE}', ephemeral=True)
    assert core.fetch_guild_welcome_message(dpytest.get_config().guilds[0].id) == new_message


@pytest.mark.asyncio
async def test_update_welcome_message_too_long(intro_cog: IntroCog, mock_interaction: MockInteraction):
    core.new_guild_welcome_message(mock_interaction.guild_id)
    await intro_cog.edit_welcome_message.callback(intro_cog, mock_interaction)
    modal = mock_interaction.response.sent_modal
    assert modal.message.max_length == 1500


@pytest.mark.asyncio
async def test_view_welcome_message(intro_cog: IntroCog, mock_interaction: MockInteraction):
    guild = dpytest.get_config().guilds[0]
    old_message = core.get_guild_welcome_message(guild.id)
    await intro_cog.view_welcome_message.callback(intro_cog, mock_interaction)
    mock_interaction.response.assert_eq(f"""Your current welcome message is:\n\r{old_message}""")
