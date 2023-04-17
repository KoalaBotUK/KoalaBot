# Futures

# Built-in/Generic Imports
import asyncio

import discord
# Libs
import discord.ext.test as dpytest
import mock
import pytest
import pytest_asyncio
import pytest_ordering as pytest
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


@pytest_asyncio.fixture
async def twitch_cog(bot: discord.ext.commands.Bot):
    """ setup any state specific to the execution of the given module."""
    twitch_cog = cog.TwitchAlert(bot)
    await bot.add_cog(twitch_cog)
    await dpytest.empty_queue()
    dpytest.configure(bot)
    return twitch_cog


@mock.patch("koalabot.check_guild_has_ext", mock.MagicMock(return_value=True))
def test_twitch_is_enabled_true(twitch_cog):
    assert cog.twitch_is_enabled(None)


@mock.patch("koalabot.is_dm_channel", mock.MagicMock(return_value=True))
def test_twitch_is_enabled_dm():
    assert not cog.twitch_is_enabled(None)


@mock.patch("koalabot.is_dm_channel", mock.MagicMock(return_value=False))
@mock.patch("koalabot.is_dpytest", False)
@pytest.mark.asyncio
async def test_twitch_is_enabled_false(twitch_cog: cog.TwitchAlert):
    last_ctx_cog = LastCtxCog(bot=twitch_cog.bot)
    await twitch_cog.bot.add_cog(last_ctx_cog)
    await dpytest.message(koalabot.COMMAND_PREFIX + "store_ctx", channel=-1)
    ctx: commands.Context = last_ctx_cog.get_last_ctx()

    assert not cog.twitch_is_enabled(ctx)


# @mock.patch("koala.utils.random_id", mock.MagicMock(return_value=7357))
@pytest.mark.asyncio(order=1)
async def test_edit_default_message_default_from_none(twitch_cog):
    this_channel = dpytest.get_config().channels[0]
    assert_embed = discord.Embed(title="Default Message Edited",
                                 description=f"Guild: {dpytest.get_config().guilds[0].id}\n"
                                             f"Channel: {this_channel.id}\n"
                                             f"Default Message: {twitch_alert.utils.DEFAULT_MESSAGE}")

    await dpytest.message(koalabot.COMMAND_PREFIX + f"twitch editMsg {this_channel.id}")
    assert dpytest.verify().message().embed(embed=assert_embed)


# @mock.patch("koala.utils.random_id", mock.MagicMock(return_value=7357))
@pytest.mark.asyncio(order=2)
async def test_edit_default_message_existing(twitch_cog):
    this_channel = dpytest.get_config().channels[0]
    assert_embed = discord.Embed(title="Default Message Edited",
                                 description=f"Guild: {dpytest.get_config().guilds[0].id}\n"
                                             f"Channel: {this_channel.id}\n"
                                             "Default Message: {user} is bad")

    await dpytest.message(koalabot.COMMAND_PREFIX + "twitch editMsg " + str(this_channel.id) + " {user} is bad")
    assert dpytest.verify().message().embed(embed=assert_embed)


@pytest.mark.asyncio(order=3)
async def test_add_user_to_twitch_alert(twitch_cog):
    assert_embed = discord.Embed(title="Added User to Twitch Alert",
                                 description=f"Channel: {dpytest.get_config().channels[0].id}\n"
                                             f"User: monstercat\n"
                                             f"Message: {twitch_alert.utils.DEFAULT_MESSAGE}",
                                 colour=KOALA_GREEN)

    await dpytest.message(
        f"{koalabot.COMMAND_PREFIX}twitch add monstercat {dpytest.get_config().channels[0].id}")
    assert dpytest.verify().message().embed(embed=assert_embed)


@pytest.mark.asyncio(order=3)
async def test_add_user_to_twitch_alert_wrong_guild(twitch_cog: twitch_alert.cog.TwitchAlert):
    guild = dpytest.backend.make_guild(name="TestGuild")
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=guild)
    dpytest.get_config().guilds.append(guild)
    dpytest.get_config().channels.append(channel)
    member = await dpytest.member_join(1, name="TestUser", discrim=1)
    await dpytest.member_join(1, dpytest.get_config().client.user)

    with pytest.raises(discord.ext.commands.errors.ChannelNotFound,
                       match=f"Channel \"{dpytest.get_config().guilds[0].channels[0].id}\" not found."):
        await dpytest.message(
        f"{koalabot.COMMAND_PREFIX}twitch add monstercat {dpytest.get_config().guilds[0].channels[0].id}",
        channel=-1, member=member)


@pytest.mark.asyncio(order=3)
async def test_add_user_to_twitch_alert_custom_message(twitch_cog: twitch_alert.cog.TwitchAlert):
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

    await dpytest.message(
        f"{koalabot.COMMAND_PREFIX}twitch add monstercat {channel.id} {test_custom_message}", channel=-1,
        member=member)
    assert dpytest.verify().message().embed(embed=assert_embed)

    sql_check_updated_server = select(UserInTwitchAlert.custom_message).where(
        and_(UserInTwitchAlert.twitch_username == 'monstercat', UserInTwitchAlert.channel_id == channel.id))
    with session_manager() as session:
        result = session.execute(sql_check_updated_server).one()
    assert result.custom_message == test_custom_message


@pytest.mark.asyncio()
async def test_remove_user_from_twitch_alert_with_message(twitch_cog: twitch_alert.cog.TwitchAlert):
    test_custom_message = "We be live gamers!"

    # Creates guild and channels and adds user and bot
    guild = dpytest.backend.make_guild(name="TestGuild")
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=guild)
    dpytest.get_config().guilds.append(guild)
    dpytest.get_config().channels.append(channel)
    member = await dpytest.member_join(-1, name="TestUser", discrim=1)
    await dpytest.member_join(-1, dpytest.get_config().client.user)

    # Creates Twitch Alert
    await dpytest.message(
        f"{koalabot.COMMAND_PREFIX}twitch add monstercat {channel.id} {test_custom_message}", channel=-1,
        member=member)

    sql_check_updated_server = select(UserInTwitchAlert.custom_message).where(and_(UserInTwitchAlert.twitch_username == 'monstercat', UserInTwitchAlert.channel_id == channel.id))
    with session_manager() as session:
        result_before = session.execute(sql_check_updated_server).one()

        assert result_before.custom_message == test_custom_message
        await dpytest.empty_queue()
        # Removes Twitch Alert
        await dpytest.message(f"{koalabot.COMMAND_PREFIX}twitch remove monstercat {channel.id}", channel=-1,
                              member=member)
        new_embed = discord.Embed(title="Removed User from Twitch Alert", colour=KOALA_GREEN,
                                  description=f"Channel: {channel.id}\n"
                                              f"User: monstercat")
        assert dpytest.verify().message().embed(new_embed)
        result_after = session.execute(sql_check_updated_server).one_or_none()
        assert result_after is None


@pytest.mark.asyncio(order=3)
async def test_remove_user_from_twitch_alert_wrong_guild(twitch_cog):
    guild = dpytest.backend.make_guild(name="TestGuild")
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=guild)
    dpytest.get_config().guilds.append(guild)
    dpytest.get_config().channels.append(channel)
    member = await dpytest.member_join(1, name="TestUser", discrim=1)
    await dpytest.member_join(1, dpytest.get_config().client.user)

    with pytest.raises(discord.ext.commands.errors.ChannelNotFound,
                       match=f"Channel \"{dpytest.get_config().channels[0].id}\" not found."):
        await dpytest.message(
        f"{koalabot.COMMAND_PREFIX}twitch remove monstercat {dpytest.get_config().channels[0].id}",
        channel=-1, member=member)


@pytest.mark.asyncio()
async def test_add_team_to_twitch_alert(twitch_cog):
    # Creates guild and channels and adds user and bot
    guild = dpytest.backend.make_guild(name="TestGuild")
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=guild)
    dpytest.get_config().guilds.append(guild)
    dpytest.get_config().channels.append(channel)
    member = await dpytest.member_join(-1, name="TestUser", discrim=1)
    await dpytest.member_join(-1, dpytest.get_config().client.user)
    assert_embed = discord.Embed(title="Added Team to Twitch Alert",
                                 description=f"Channel: {channel.id}\n"
                                             f"Team: faze\n"
                                             f"Message: {twitch_alert.utils.DEFAULT_MESSAGE}",
                                 colour=KOALA_GREEN)
    # Creates Twitch Alert
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}twitch addTeam faze {channel.id}", channel=-1,
                          member=member)
    assert dpytest.verify().message().embed(assert_embed)


@pytest.mark.asyncio()
async def test_add_team_to_twitch_alert_with_message(twitch_cog):
    # Creates guild and channels and adds user and bot
    guild = dpytest.backend.make_guild(name="TestGuild")
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=guild)
    dpytest.get_config().guilds.append(guild)
    dpytest.get_config().channels.append(channel)
    member = await dpytest.member_join(-1, name="TestUser", discrim=1)
    await dpytest.member_join(-1, dpytest.get_config().client.user)
    assert_embed = discord.Embed(title="Added Team to Twitch Alert",
                                 description=f"Channel: {channel.id}\n"
                                             f"Team: faze\n"
                                             f"Message: wooo message",
                                 colour=KOALA_GREEN)
    # Creates Twitch Alert
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}twitch addTeam faze {channel.id} wooo message",
                          channel=-1, member=member)
    assert dpytest.verify().message().embed(assert_embed)


@pytest.mark.asyncio()
async def test_add_team_to_twitch_alert_wrong_guild(twitch_cog):
    # Creates guild and channels and adds user and bot
    guild = dpytest.backend.make_guild(name="TestGuild")
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=guild)
    dpytest.get_config().guilds.append(guild)
    dpytest.get_config().channels.append(channel)
    member = await dpytest.member_join(-1, name="TestUser", discrim=1)
    await dpytest.member_join(-1, dpytest.get_config().client.user)
    # Creates Twitch Alert
    with pytest.raises(discord.ext.commands.errors.ChannelNotFound,
                       match=f"Channel \"{dpytest.get_config().channels[0].id}\" not found."):
        await dpytest.message(
        f"{koalabot.COMMAND_PREFIX}twitch addTeam faze {dpytest.get_config().channels[0].id}",
        channel=-1, member=member)


@pytest.mark.asyncio()
async def test_remove_team_from_twitch_alert_with_message(twitch_cog):
    test_custom_message = "We be live gamers!"

    # Creates guild and channels and adds user and bot
    guild = dpytest.backend.make_guild(name="TestGuild")
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=guild)
    dpytest.get_config().guilds.append(guild)
    dpytest.get_config().channels.append(channel)
    member = await dpytest.member_join(-1, name="TestUser", discrim=1)
    await dpytest.member_join(-1, dpytest.get_config().client.user)

    # Creates Twitch Alert
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}twitch addTeam faze {channel.id} {test_custom_message}",
                          channel=-1, member=member)
    await dpytest.empty_queue()
    # Removes Twitch Alert
    await dpytest.message(f"{koalabot.COMMAND_PREFIX}twitch removeTeam faze {channel.id}", channel=-1,
                          member=member)
    new_embed = discord.Embed(title="Removed Team from Twitch Alert", colour=KOALA_GREEN,
                              description=f"Channel: {channel.id}\n"
                                          f"Team: faze")
    assert dpytest.verify().message().embed(new_embed)
    pass


@pytest.mark.asyncio(order=3)
async def test_remove_team_from_twitch_alert_wrong_guild(twitch_cog):
    guild = dpytest.backend.make_guild(name="TestGuild")
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=guild)
    dpytest.get_config().guilds.append(guild)
    dpytest.get_config().channels.append(channel)
    member = await dpytest.member_join(1, name="TestUser", discrim=1)
    await dpytest.member_join(1, dpytest.get_config().client.user)

    with pytest.raises(discord.ext.commands.errors.ChannelNotFound,
                       match=f"Channel \"{dpytest.get_config().channels[0].id}\" not found."):
        await dpytest.message(
        f"{koalabot.COMMAND_PREFIX}twitch addTeam faze {dpytest.get_config().channels[0].id}",
        channel=-1, member=member)


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
    this_channel = dpytest.get_config().channels[0]
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


