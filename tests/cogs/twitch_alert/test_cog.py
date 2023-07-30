# Futures

# Built-in/Generic Imports
import asyncio

import discord
# Libs
import discord.ext.test as dpytest
import mock
import pytest
import pytest_asyncio
from discord.ext import commands
from sqlalchemy import select, and_

# Own modules
import koalabot
from koala.cogs import twitch_alert
from koala.cogs.twitch_alert import cog
from koala.cogs.twitch_alert.models import UserInTwitchAlert
from koala.colours import KOALA_GREEN
from koala.db import session_manager
from tests.tests_utils.last_ctx_cog import LastCtxCog

# Constants
DB_PATH = "Koala.db"


# Variables

@pytest.mark.asyncio
async def test_setup(bot):
    with mock.patch.object(discord.ext.commands.bot.Bot, 'add_cog') as mock1:
        await cog.setup(bot)
    mock1.assert_called()


@pytest_asyncio.fixture(name="twitch_cog")
async def twitch_cog_fixture(bot: discord.ext.commands.Bot):
    """ setup any state specific to the execution of the given module."""
    t_cog = cog.TwitchAlert(bot)
    await bot.add_cog(t_cog)
    await dpytest.empty_queue()
    dpytest.configure(bot)
    return t_cog


@pytest.mark.order(1)
@pytest.mark.asyncio
async def test_edit_default_message_default_from_none(twitch_cog: cog.TwitchAlert, mock_interaction):
    this_channel = dpytest.get_config().channels[0]
    assert_embed = discord.Embed(title="Default Message Edited",
                                 description=f"Guild: {dpytest.get_config().guilds[0].id}\n"
                                             f"Channel: {this_channel.id}\n"
                                             f"Default Message: {twitch_alert.utils.DEFAULT_MESSAGE}")

    await twitch_cog.edit_default_message.callback(twitch_cog, mock_interaction, this_channel)
    mock_interaction.response.assert_eq(embed=assert_embed)


@pytest.mark.order(2)
@pytest.mark.asyncio
async def test_edit_default_message_existing(twitch_cog: cog.TwitchAlert, mock_interaction):
    this_channel = dpytest.get_config().channels[0]
    assert_embed = discord.Embed(title="Default Message Edited",
                                 description=f"Guild: {dpytest.get_config().guilds[0].id}\n"
                                             f"Channel: {this_channel.id}\n"
                                             "Default Message: {user} is bad")

    await twitch_cog.edit_default_message.callback(twitch_cog, mock_interaction, this_channel, "{user} is bad")
    mock_interaction.response.assert_eq(embed=assert_embed)


@pytest.mark.order(3)
@pytest.mark.asyncio
async def test_add_user_to_twitch_alert(twitch_cog: cog.TwitchAlert, mock_interaction):
    assert_embed = discord.Embed(title="Added User to Twitch Alert",
                                 description=f"Channel: {dpytest.get_config().channels[0].id}\n"
                                             f"User: monstercat\n"
                                             f"Message: {twitch_alert.utils.DEFAULT_MESSAGE}",
                                 colour=KOALA_GREEN)

    await twitch_cog.add_user_to_twitch_alert.callback(twitch_cog, mock_interaction,
                                                       "monstercat", dpytest.get_config().channels[0])
    mock_interaction.response.assert_eq(embed=assert_embed)


@pytest.mark.order(3)
@pytest.mark.asyncio
async def test_add_user_to_twitch_alert_custom_message(twitch_cog: cog.TwitchAlert, mock_interaction):
    test_custom_message = "We be live gamers!"

    guild = dpytest.backend.make_guild(name="TestGuild")
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=guild)
    dpytest.get_config().guilds.append(guild)
    dpytest.get_config().channels.append(channel)
    member = await dpytest.member_join(-1, name="TestUser", discrim=1)
    await dpytest.member_join(-1, dpytest.get_config().client.user)

    assert_embed = discord.Embed(title="Added User to Twitch Alert",
                                 description=f"Channel: {channel.id}\n"
                                             f"User: monstercat\n"
                                             f"Message: {test_custom_message}",
                                 colour=KOALA_GREEN)

    await twitch_cog.add_user_to_twitch_alert.callback(twitch_cog, mock_interaction,
                                                       "monstercat", channel, test_custom_message)
    mock_interaction.response.assert_eq(embed=assert_embed)

    sql_check_updated_server = select(UserInTwitchAlert.custom_message).where(
        and_(UserInTwitchAlert.twitch_username == 'monstercat', UserInTwitchAlert.channel_id == channel.id))
    with session_manager() as session:
        result = session.execute(sql_check_updated_server).one()
    assert result.custom_message == test_custom_message


@pytest.mark.asyncio()
async def test_remove_user_from_twitch_alert_with_message(twitch_cog: cog.TwitchAlert, mock_interaction):
    test_custom_message = "We be live gamers!"

    # Creates guild and channels and adds user and bot
    guild = dpytest.backend.make_guild(name="TestGuild")
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=guild)
    dpytest.get_config().guilds.append(guild)
    dpytest.get_config().channels.append(channel)
    member = await dpytest.member_join(-1, name="TestUser", discrim=1)
    await dpytest.member_join(-1, dpytest.get_config().client.user)

    # Creates Twitch Alert
    await twitch_cog.add_user_to_twitch_alert.callback(twitch_cog, mock_interaction, "monstercat", channel, test_custom_message)

    sql_check_updated_server = select(UserInTwitchAlert.custom_message).where(
        and_(UserInTwitchAlert.twitch_username == 'monstercat', UserInTwitchAlert.channel_id == channel.id))
    with session_manager() as session:
        result_before = session.execute(sql_check_updated_server).one()

        assert result_before.custom_message == test_custom_message
        await dpytest.empty_queue()
        # Removes Twitch Alert
        await twitch_cog.remove_user_from_twitch_alert.callback(twitch_cog, mock_interaction, "monstercat", channel)
        new_embed = discord.Embed(title="Removed User from Twitch Alert", colour=KOALA_GREEN,
                                  description=f"Channel: {channel.id}\n"
                                              f"User: monstercat")
        mock_interaction.response.assert_eq(embed=new_embed)
        result_after = session.execute(sql_check_updated_server).one_or_none()
        assert result_after is None


@pytest.mark.asyncio()
async def test_add_team_to_twitch_alert(twitch_cog: cog.TwitchAlert, mock_interaction):
    # Creates guild and channels and adds user and bot
    guild = dpytest.backend.make_guild(name="TestGuild")
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=guild)
    dpytest.get_config().guilds.append(guild)
    dpytest.get_config().channels.append(channel)
    await dpytest.member_join(-1, dpytest.get_config().client.user)
    assert_embed = discord.Embed(title="Added Team to Twitch Alert",
                                 description=f"Channel: {channel.id}\n"
                                             f"Team: faze\n"
                                             f"Message: {twitch_alert.utils.DEFAULT_MESSAGE}",
                                 colour=KOALA_GREEN)
    # Creates Twitch Alert
    await twitch_cog.add_team_to_twitch_alert.callback(twitch_cog, mock_interaction, "faze", channel)
    mock_interaction.response.assert_eq(embed=assert_embed)


@pytest.mark.asyncio()
async def test_add_team_to_twitch_alert_with_message(twitch_cog: cog.TwitchAlert, mock_interaction):
    # Creates guild and channels and adds user and bot
    guild = dpytest.backend.make_guild(name="TestGuild")
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=guild)
    dpytest.get_config().guilds.append(guild)
    dpytest.get_config().channels.append(channel)
    await dpytest.member_join(-1, dpytest.get_config().client.user)
    assert_embed = discord.Embed(title="Added Team to Twitch Alert",
                                 description=f"Channel: {channel.id}\n"
                                             f"Team: faze\n"
                                             f"Message: wooo message",
                                 colour=KOALA_GREEN)
    # Creates Twitch Alert
    await twitch_cog.add_team_to_twitch_alert.callback(twitch_cog, mock_interaction, "faze", channel, "wooo message")
    mock_interaction.response.assert_eq(embed=assert_embed)


@pytest.mark.asyncio()
async def test_remove_team_from_twitch_alert_with_message(twitch_cog: cog.TwitchAlert, mock_interaction):
    test_custom_message = "We be live gamers!"

    # Creates guild and channels and adds user and bot
    guild = dpytest.backend.make_guild(name="TestGuild")
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=guild)
    dpytest.get_config().guilds.append(guild)
    dpytest.get_config().channels.append(channel)
    await dpytest.member_join(-1, dpytest.get_config().client.user)

    # Creates Twitch Alert
    await twitch_cog.add_team_to_twitch_alert.callback(twitch_cog, mock_interaction, "faze", channel,
                                                       test_custom_message)
    await dpytest.empty_queue()
    # Removes Twitch Alert
    await twitch_cog.remove_team_from_twitch_alert.callback(twitch_cog, mock_interaction, "faze", channel)
    new_embed = discord.Embed(title="Removed Team from Twitch Alert", colour=KOALA_GREEN,
                              description=f"Channel: {channel.id}\n"
                                          f"Team: faze")
    mock_interaction.response.assert_eq(embed=new_embed)


@pytest.mark.asyncio()
@pytest.mark.first
async def test_on_ready(twitch_cog: twitch_alert.cog.TwitchAlert):
    with mock.patch.object(twitch_alert.cog.TwitchAlert, 'start_loops') as mock1:
        await twitch_cog.on_ready()
    mock1.assert_called_with()


@mock.patch("koala.utils.random_id", mock.MagicMock(return_value=7363))
@mock.patch("cogs.twitch_alert.TwitchAPIHandler.get_streams_data",
            mock.MagicMock(return_value={'id': '3215560150671170227', 'user_id': '27446517',
                                         "user_name": "Monstercat", 'game_id': "26936", 'type': 'live',
                                         'title': 'Music 24/7'}))
@pytest.mark.skip(reason="Issues with testing inside asyncio event loop, not implemented")
@pytest.mark.asyncio
async def test_loop_check_live(twitch_cog: twitch_alert.cog.TwitchAlert):
    expected_embed = discord.Embed(colour=koalabot.KOALA_GREEN,
                                   title="<:twitch:734024383957434489>  Monstercat is now streaming!",
                                   description="https://twitch.tv/monstercat")
    expected_embed.add_field(name="Stream Title", value="Non Stop Music - Monstercat Radio :notes:")
    expected_embed.add_field(name="Playing", value="Music & Performing Arts")
    expected_embed.set_thumbnail(url="https://static-cdn.jtvnw.net/jtv_user_pictures/"
                                     "monstercat-profile_image-3e109d75f8413319-300x300.jpeg")

    await dpytest.message(f"{koalabot.COMMAND_PREFIX}twitch add monstercat 7363")
    await dpytest.empty_queue()
    twitch_cog.start_loop()
    await asyncio.sleep(10)
    assert dpytest.verify().message().embed(expected_embed)


@pytest.mark.skip(reason="Issues with testing inside asyncio event loop, not implemented")
@pytest.mark.asyncio
async def test_loop_check_team_live(twitch_cog):
    assert False, "Not Implemented"
