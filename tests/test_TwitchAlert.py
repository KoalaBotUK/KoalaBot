#!/usr/bin/env python

"""
Testing KoalaBot TwitchAlert

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import os
import asyncio

# Libs
import discord.ext.test as dpytest
import mock
import pytest_ordering as pytest
import pytest
import discord
from discord.ext import commands

# Own modules
import KoalaBot
from cogs import TwitchAlert
from utils import KoalaDBManager
from utils.KoalaColours import *

# Constants
DB_PATH = "KoalaBotTwitchTest.db"


# Variables


def setup_module():
    try:
        if os.name == 'nt':
            print("Windows Detected: Deleting windows_"+DB_PATH)
            os.remove("windows_"+DB_PATH)
        else:
            print("Windows Not Detected: Deleting "+DB_PATH)
            os.remove(DB_PATH)
        KoalaBot.is_dpytest = True
    except FileNotFoundError:
        print("Database Doesn't Exist, Continuing")
    finally:
        print("Setup Module")


def test_create_live_embed():
    # Create the expected embed with information required
    expected = discord.Embed(colour=KOALA_GREEN, title="https://twitch.tv/test")
    expected.set_author(name="Test is now streaming!", icon_url=TwitchAlert.TWITCH_ICON)
    expected.add_field(name="Stream Title", value="Test Title")
    expected.add_field(name="Playing", value="TestGame")
    expected.set_thumbnail(url="http://koalabot.uk")

    # Create JSON required to pass to method
    stream_info = {'user_name': "Test", 'user_login': "test", 'title': "Test Title"}
    user_info = {'profile_image_url': "http://koalabot.uk"}
    game_info = {'name': "TestGame"}

    # Get response and assert equal
    result = TwitchAlert.create_live_embed(stream_info, user_info, game_info, "")
    assert dpytest.embed_eq(result, expected)


def test_create_live_embed_with_message():
    # Create the expected embed with information required
    expected = discord.Embed(colour=KOALA_GREEN, title="https://twitch.tv/test", description="Hello Message")
    expected.set_author(name="Test is now streaming!", icon_url=TwitchAlert.TWITCH_ICON)
    expected.add_field(name="Stream Title", value="Test Title")
    expected.add_field(name="Playing", value="TestGame")
    expected.set_thumbnail(url="http://koalabot.uk")

    # Create JSON required to pass to method
    stream_info = {'user_name': "Test", 'user_login': "test", 'title': "Test Title"}
    user_info = {'profile_image_url': "http://koalabot.uk"}
    game_info = {'name': "TestGame"}

    # Get response and assert equal
    result = TwitchAlert.create_live_embed(stream_info, user_info, game_info, "Hello Message")
    assert dpytest.embed_eq(result, expected)


@pytest.mark.asyncio
async def test_setup():
    with mock.patch.object(discord.ext.commands.bot.Bot, 'add_cog') as mock1:
        TwitchAlert.setup(KoalaBot.client)
    mock1.assert_called()


# Test TwitchAlert
@pytest.fixture
async def twitch_cog(bot):
    """ setup any state specific to the execution of the given module."""
    twitch_cog = TwitchAlert.TwitchAlert(bot)
    bot.add_cog(twitch_cog)
    await dpytest.empty_queue()
    dpytest.configure(bot)
    return twitch_cog


@mock.patch("utils.KoalaUtils.random_id", mock.MagicMock(return_value=7357))
@pytest.mark.asyncio(order=1)
async def test_edit_default_message_default_from_none(twitch_cog):
    this_channel = dpytest.get_config().channels[0]
    assert_embed = discord.Embed(title="Default Message Edited",
                                 description=f"Guild: {dpytest.get_config().guilds[0].id}\n"
                                             f"Channel: {this_channel.id}\n"
                                             f"Default Message: {TwitchAlert.DEFAULT_MESSAGE}")

    await dpytest.message(KoalaBot.COMMAND_PREFIX + f"edit_default_message {this_channel.id}")
    assert dpytest.verify().message().embed(embed=assert_embed)


@mock.patch("utils.KoalaUtils.random_id", mock.MagicMock(return_value=7357))
@pytest.mark.asyncio(order=2)
async def test_edit_default_message_existing(twitch_cog):
    this_channel = dpytest.get_config().channels[0]
    assert_embed = discord.Embed(title="Default Message Edited",
                                 description=f"Guild: {dpytest.get_config().guilds[0].id}\n"
                                             f"Channel: {this_channel.id}\n"
                                             "Default Message: {user} is bad")

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "edit_default_message " + str(this_channel.id) + " {user} is bad")
    assert dpytest.verify().message().embed(embed=assert_embed)


@pytest.mark.asyncio(order=3)
async def test_add_user_to_twitch_alert(twitch_cog):
    assert_embed = discord.Embed(title="Added User to Twitch Alert",
                                 description=f"Channel: {dpytest.get_config().channels[0].id}\n"
                                             f"User: monstercat\n"
                                             f"Message: {TwitchAlert.DEFAULT_MESSAGE}",
                                 colour=KOALA_GREEN)

    await dpytest.message(
        f"{KoalaBot.COMMAND_PREFIX}add_user_to_twitch_alert {dpytest.get_config().channels[0].id} monstercat")
    assert dpytest.verify().message().embed(embed=assert_embed)


@pytest.mark.asyncio(order=3)
async def test_add_user_to_twitch_alert_wrong_guild(twitch_cog):
    guild = dpytest.backend.make_guild(name="TestGuild")
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=guild)
    dpytest.get_config().guilds.append(guild)
    dpytest.get_config().channels.append(channel)
    member = await dpytest.member_join(1, name="TestUser", discrim=1)
    await dpytest.member_join(1, dpytest.get_config().client.user)

    await dpytest.message(
        f"{KoalaBot.COMMAND_PREFIX}add_user_to_twitch_alert {dpytest.get_config().channels[0].id} monstercat",
        channel=-1, member=member)
    assert dpytest.verify().message().embed(
        embed=TwitchAlert.error_embed("The channel ID provided is either invalid, or not in this server."))


@pytest.mark.asyncio(order=3)
async def test_add_user_to_twitch_alert_custom_message(twitch_cog):
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
        f"{KoalaBot.COMMAND_PREFIX}add_user_to_twitch_alert {channel.id} monstercat {test_custom_message}", channel=-1,
        member=member)
    assert dpytest.verify().message().embed(embed=assert_embed)

    sql_check_updated_server = f"SELECT custom_message FROM UserInTwitchAlert WHERE twitch_username='monstercat' AND channel_id={channel.id}"
    assert twitch_cog.ta_database_manager.database_manager.db_execute_select(sql_check_updated_server) == [
        (test_custom_message,)]


@pytest.mark.asyncio()
async def test_remove_user_from_twitch_alert_with_message(twitch_cog):
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
        f"{KoalaBot.COMMAND_PREFIX}add_user_to_twitch_alert {channel.id} monstercat {test_custom_message}", channel=-1,
        member=member)

    sql_check_updated_server = f"SELECT custom_message FROM UserInTwitchAlert WHERE twitch_username='monstercat' AND channel_id={channel.id}"
    assert twitch_cog.ta_database_manager.database_manager.db_execute_select(sql_check_updated_server) == [
        (test_custom_message,)]
    await dpytest.empty_queue()
    # Removes Twitch Alert
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}remove_user_from_twitch_alert {channel.id} monstercat", channel=-1,
                          member=member)
    new_embed = discord.Embed(title="Removed User from Twitch Alert", colour=KOALA_GREEN,
                              description=f"Channel: {channel.id}\n"
                                          f"User: monstercat")
    assert dpytest.verify().message().embed(new_embed)
    assert twitch_cog.ta_database_manager.database_manager.db_execute_select(sql_check_updated_server) == []
    pass


@pytest.mark.asyncio(order=3)
async def test_remove_user_from_twitch_alert_wrong_guild(twitch_cog):
    guild = dpytest.backend.make_guild(name="TestGuild")
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=guild)
    dpytest.get_config().guilds.append(guild)
    dpytest.get_config().channels.append(channel)
    member = await dpytest.member_join(1, name="TestUser", discrim=1)
    await dpytest.member_join(1, dpytest.get_config().client.user)

    await dpytest.message(
        f"{KoalaBot.COMMAND_PREFIX}remove_user_from_twitch_alert {dpytest.get_config().channels[0].id} monstercat",
        channel=-1, member=member)
    assert dpytest.verify().message().embed(
        embed=TwitchAlert.error_embed("The channel ID provided is either invalid, or not in this server."))


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
                                             f"Message: {TwitchAlert.DEFAULT_MESSAGE}",
                                 colour=KOALA_GREEN)
    # Creates Twitch Alert
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}add_team_to_twitch_alert {channel.id} faze", channel=-1,
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
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}add_team_to_twitch_alert {channel.id} faze wooo message",
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
    await dpytest.message(
        f"{KoalaBot.COMMAND_PREFIX}add_team_to_twitch_alert {dpytest.get_config().channels[0].id} faze ", channel=-1,
        member=member)
    assert dpytest.verify().message().embed(
        embed=TwitchAlert.error_embed("The channel ID provided is either invalid, or not in this server."))


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
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}add_team_to_twitch_alert {channel.id} faze {test_custom_message}",
                          channel=-1, member=member)
    await dpytest.empty_queue()
    # Removes Twitch Alert
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}remove_team_from_twitch_alert {channel.id} faze", channel=-1,
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

    await dpytest.message(
        f"{KoalaBot.COMMAND_PREFIX}remove_team_from_twitch_alert {dpytest.get_config().channels[0].id} monstercat",
        channel=-1, member=member)
    assert dpytest.verify().message().embed(
        embed=TwitchAlert.error_embed("The channel ID provided is either invalid, or not in this server."))


@pytest.mark.asyncio()
@pytest.mark.first
async def test_on_ready(twitch_cog: TwitchAlert.TwitchAlert):
    with mock.patch.object(TwitchAlert.TwitchAlert, 'start_loops') as mock1:
        await twitch_cog.on_ready()
    mock1.assert_called_with()


@mock.patch("utils.KoalaUtils.random_id", mock.MagicMock(return_value=7363))
@mock.patch("cogs.TwitchAlert.TwitchAPIHandler.get_streams_data",
            mock.MagicMock(return_value={'id': '3215560150671170227', 'user_id': '27446517',
                                         "user_name": "Monstercat", 'game_id': "26936", 'type': 'live',
                                         'title': 'Music 24/7'}))
@pytest.mark.skip(reason="Issues with testing inside asyncio event loop, not implemented")
@pytest.mark.asyncio
async def test_loop_check_live(twitch_cog):
    this_channel = dpytest.get_config().channels[0]
    expected_embed = discord.Embed(colour=KoalaBot.KOALA_GREEN,
                                   title="<:twitch:734024383957434489>  Monstercat is now streaming!",
                                   description="https://twitch.tv/monstercat")
    expected_embed.add_field(name="Stream Title", value="Non Stop Music - Monstercat Radio :notes:")
    expected_embed.add_field(name="Playing", value="Music & Performing Arts")
    expected_embed.set_thumbnail(url="https://static-cdn.jtvnw.net/jtv_user_pictures/"
                                     "monstercat-profile_image-3e109d75f8413319-300x300.jpeg")

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "create_twitch_alert")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}add_twitch_alert_to_channel 7363 {this_channel.id}")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}add_user_to_twitch_alert 7363 monstercat")
    await dpytest.empty_queue()
    twitch_cog.start_loop()
    await asyncio.sleep(10)
    assert dpytest.verify().message().embed(expected_embed)


@pytest.mark.asyncio
async def test_create_alert_embed(twitch_cog):
    stream_data = {'id': '3215560150671170227', 'user_id': '27446517',
                   "user_name": "Monstercat", 'user_login': "monstercat", 'game_id': "26936", 'type': 'live',
                   'title': 'Music 24/7'}

    assert type(await twitch_cog.create_alert_embed(stream_data, None)) is discord.Embed


@pytest.mark.skip(reason="Issues with testing inside asyncio event loop, not implemented")
@pytest.mark.asyncio
async def test_loop_check_team_live(twitch_cog):
    assert False, "Not Implemented"


# Test TwitchAPIHandler

@pytest.fixture
def twitch_api_handler():
    return TwitchAlert.TwitchAPIHandler(TwitchAlert.TWITCH_CLIENT_ID, TwitchAlert.TWITCH_SECRET)


@pytest.mark.asyncio
async def test_get_new_twitch_oauth(twitch_api_handler):
    assert await twitch_api_handler.get_new_twitch_oauth() is not None


@pytest.mark.asyncio
async def test_requests_get(twitch_api_handler):
    assert (await twitch_api_handler.requests_get("https://api.twitch.tv/helix/streams?",
                                           params=(('user_login', 'monstercat'),))).get("data") is not None


@pytest.mark.asyncio
async def test_get_streams_data(twitch_api_handler):
    usernames = ['monstercat', 'jaydwee']
    streams_data = await twitch_api_handler.get_streams_data(usernames)
    assert streams_data is not None


@pytest.mark.asyncio
async def test_get_user_data(twitch_api_handler):
    assert await twitch_api_handler.get_user_data('monstercat') is not None


@pytest.mark.asyncio
async def test_get_game_data(twitch_api_handler):
    assert 'music' in (await twitch_api_handler.get_game_data('26936')).get('name').lower()


@pytest.mark.asyncio
async def test_get_team_users(twitch_api_handler):
    # assumes uosvge is in the team called uosvge
    members = await twitch_api_handler.get_team_users('uosvge')
    for member in members:
        if member.get('user_login') == 'uosvge':
            assert True
            return
    assert False


# Test TwitchAlertDBManager
@pytest.fixture
def twitch_alert_db_manager(twitch_cog):
    return TwitchAlert.TwitchAlertDBManager(KoalaDBManager.KoalaDBManager(DB_PATH, KoalaBot.DB_KEY, KoalaBot.config_dir), twitch_cog.bot)


@pytest.fixture
def twitch_alert_db_manager_tables(twitch_alert_db_manager):
    twitch_alert_db_manager.create_tables()
    return twitch_alert_db_manager


def test_get_parent_database_manager(twitch_alert_db_manager):
    assert isinstance(twitch_alert_db_manager.get_parent_database_manager(), KoalaDBManager.KoalaDBManager)


@pytest.mark.first
def test_before_create_tables(twitch_alert_db_manager):
    setup_module()
    parent_database_manager = twitch_alert_db_manager.get_parent_database_manager()
    sql_check_table_exists = """SELECT name FROM sqlite_master WHERE type='table' AND name='TwitchAlerts';"""
    assert parent_database_manager.db_execute_select(sql_check_table_exists) == []


def test_create_tables(twitch_alert_db_manager):
    parent_database_manager = twitch_alert_db_manager.get_parent_database_manager()
    twitch_alert_db_manager.create_tables()
    for table in ["TwitchAlerts", "UserInTwitchAlert",
                  "TeamInTwitchAlert", "UserInTwitchTeam"]:
        sql_check_table_exists = f"""SELECT name FROM sqlite_master WHERE type='table' AND name={table};"""
        assert parent_database_manager.db_execute_select(sql_check_table_exists) != []


def test_new_ta(twitch_alert_db_manager_tables):
    assert TwitchAlert.DEFAULT_MESSAGE == twitch_alert_db_manager_tables.new_ta(guild_id=1234, channel_id=2345)
    sql_check_db_updated = f"SELECT guild_id,default_message FROM TwitchAlerts WHERE channel_id = 2345"
    assert twitch_alert_db_manager_tables.database_manager.db_execute_select(sql_check_db_updated) == \
           [(1234, TwitchAlert.DEFAULT_MESSAGE)]


def test_new_ta_message(twitch_alert_db_manager_tables):
    test_message = "Test message"
    assert test_message == twitch_alert_db_manager_tables.new_ta(guild_id=12345, channel_id=23456,
                                                                 default_message=test_message)
    sql_check_db_updated = f"SELECT guild_id,default_message FROM TwitchAlerts WHERE channel_id = 23456"
    assert twitch_alert_db_manager_tables.database_manager.db_execute_select(sql_check_db_updated) == \
           [(12345, test_message,)]


def test_new_ta_replace(twitch_alert_db_manager_tables):
    test_message = "Test message"
    test_new_ta_message(twitch_alert_db_manager_tables=twitch_alert_db_manager_tables)
    assert test_message == twitch_alert_db_manager_tables.new_ta(guild_id=1234, channel_id=2345,
                                                                 default_message=test_message, replace=True)
    sql_check_db_updated = f"SELECT guild_id,default_message FROM TwitchAlerts WHERE channel_id = 2345"
    assert twitch_alert_db_manager_tables.database_manager.db_execute_select(sql_check_db_updated) == \
           [(1234, test_message)]
    pass


def test_add_user_to_ta_default_message(twitch_alert_db_manager_tables):
    twitch_alert_db_manager_tables.new_ta(1234, 1234567891, None)
    twitch_alert_db_manager_tables.add_user_to_ta(1234567891, "monstercat", None)
    parent_database_manager = twitch_alert_db_manager_tables.get_parent_database_manager()
    sql_find_twitch_alert = f"""SELECT twitch_username, custom_message
                                FROM UserInTwitchAlert
                                WHERE channel_id = 1234567891 AND twitch_username = 'monstercat'"""
    result = parent_database_manager.db_execute_select(sql_find_twitch_alert)
    assert result[0][0] == "monstercat"
    assert result[0][1] is None


def test_add_user_to_ta_custom_message(twitch_alert_db_manager_tables):
    twitch_alert_db_manager_tables.new_ta(1234, 1234567892, None)
    twitch_alert_db_manager_tables.add_user_to_ta(1234567892, "monstercat", "FiddleSticks {user} is live!")
    parent_database_manager = twitch_alert_db_manager_tables.get_parent_database_manager()
    sql_find_twitch_alert = f"""SELECT twitch_username, custom_message
                                FROM UserInTwitchAlert
                                WHERE channel_id = 1234567892 AND twitch_username = 'monstercat'"""
    result = parent_database_manager.db_execute_select(sql_find_twitch_alert)
    assert result[0][0] == "monstercat"
    assert result[0][1] == "FiddleSticks {user} is live!"


@pytest.mark.asyncio()
async def test_remove_user_from_ta(twitch_alert_db_manager_tables):
    test_add_user_to_ta_default_message(twitch_alert_db_manager_tables)
    await twitch_alert_db_manager_tables.remove_user_from_ta(1234567891, "monstercat")
    parent_database_manager = twitch_alert_db_manager_tables.get_parent_database_manager()
    sql_find_twitch_alert = f"""SELECT twitch_username, custom_message
                                FROM UserInTwitchAlert
                                WHERE channel_id = 1234567891 AND twitch_username = 'monstercat'"""
    assert parent_database_manager.db_execute_select(sql_find_twitch_alert) == []


@pytest.mark.asyncio()
async def test_delete_message(twitch_alert_db_manager_tables):
    with mock.patch.object(discord.TextChannel, 'fetch_message') as mock1:
        await twitch_alert_db_manager_tables.delete_message(1234, dpytest.get_config().channels[0].id)
    mock1.assert_called_with(1234)


def test_add_team_to_ta(twitch_alert_db_manager_tables):
    twitch_alert_db_manager_tables.add_team_to_ta(channel_id=566, twitch_team="faze", custom_message=None, guild_id=568)
    sql_select_team = "SELECT custom_message FROM TeamInTwitchAlert " \
                      "WHERE channel_id = 566 AND twitch_team_name = 'faze'"
    assert twitch_alert_db_manager_tables.get_parent_database_manager().db_execute_select(sql_select_team) == [(None,)]


def test_add_team_to_ta_custom_message(twitch_alert_db_manager_tables, channel_id=573, guild_id=574):
    twitch_alert_db_manager_tables.add_team_to_ta(channel_id=channel_id, twitch_team="faze",
                                                  custom_message="Message here", guild_id=guild_id)
    sql_select_team = "SELECT custom_message FROM TeamInTwitchAlert " \
                      f"WHERE channel_id = {channel_id} AND twitch_team_name = 'faze'"
    assert twitch_alert_db_manager_tables.get_parent_database_manager().db_execute_select(sql_select_team) == \
           [("Message here",)]

@pytest.mark.asyncio()
async def test_remove_team_from_ta(twitch_alert_db_manager_tables):
    test_add_team_to_ta_custom_message(twitch_alert_db_manager_tables, channel_id=590, guild_id=591)
    await twitch_alert_db_manager_tables.remove_team_from_ta(590, "faze")
    sql_select_team = "SELECT custom_message FROM TeamInTwitchAlert " \
                      "WHERE channel_id = 590 AND twitch_team_name = 'faze'"
    assert twitch_alert_db_manager_tables.get_parent_database_manager().db_execute_select(sql_select_team) == []


@pytest.mark.asyncio()
async def test_remove_team_from_ta_invalid(twitch_alert_db_manager_tables):
    with pytest.raises(AttributeError,
                       match="Team name not found"):
        await twitch_alert_db_manager_tables.remove_team_from_ta(590, 590)


@pytest.mark.asyncio()
async def test_remove_team_from_ta_deletes_messages(twitch_alert_db_manager_tables):
    await test_update_team_members(twitch_alert_db_manager_tables)
    sql_add_message = "UPDATE UserInTwitchTeam SET message_id = 1 " \
                      "WHERE team_twitch_alert_id = 604 AND twitch_username = 'monstercat'"
    twitch_alert_db_manager_tables.get_parent_database_manager().db_execute_commit(sql_add_message)
    with mock.patch.object(TwitchAlert.TwitchAlertDBManager, 'delete_message') as mock1:
        await twitch_alert_db_manager_tables.remove_team_from_ta(605, "monstercat")
    mock1.assert_called_with(1, 605)


@pytest.mark.asyncio()
async def test_update_team_members(twitch_alert_db_manager_tables):
    sql_insert_monstercat_team = "INSERT INTO TeamInTwitchAlert(team_twitch_alert_id,channel_id,twitch_team_name) " \
                                 "VALUES(604,605,'monstercat')"
    twitch_alert_db_manager_tables.get_parent_database_manager().db_execute_commit(sql_insert_monstercat_team)
    await twitch_alert_db_manager_tables.update_team_members(604, "monstercat")
    sql_select_monstercat_team = "SELECT twitch_username " \
                                 "FROM UserInTwitchTeam " \
                                 "WHERE team_twitch_alert_id = 604 AND twitch_username='monstercat'"
    result = twitch_alert_db_manager_tables.get_parent_database_manager().db_execute_select(sql_select_monstercat_team)
    assert result != []
    pass


@pytest.mark.asyncio()
async def test_update_all_teams_members(twitch_alert_db_manager_tables):
    sql_insert_monstercat_team = "INSERT INTO TeamInTwitchAlert(team_twitch_alert_id,channel_id,twitch_team_name) " \
                                 "VALUES(614,615,'monstercat')"
    twitch_alert_db_manager_tables.get_parent_database_manager().db_execute_commit(sql_insert_monstercat_team)
    sql_insert_monstercat_team = "INSERT INTO TeamInTwitchAlert(team_twitch_alert_id,channel_id,twitch_team_name) " \
                                 "VALUES(616,617,'monstercat')"
    twitch_alert_db_manager_tables.get_parent_database_manager().db_execute_commit(sql_insert_monstercat_team)
    await twitch_alert_db_manager_tables.update_all_teams_members()
    sql_select_monstercats_team = "SELECT twitch_username " \
                                  "FROM UserInTwitchTeam " \
                                  "WHERE (team_twitch_alert_id = 614 OR team_twitch_alert_id = 616) " \
                                  "AND twitch_username='monstercat'"
    result = twitch_alert_db_manager_tables.get_parent_database_manager().db_execute_select(sql_select_monstercats_team)
    assert len(result) == 2
    pass


@pytest.mark.asyncio()
async def test_delete_all_offline_streams(twitch_alert_db_manager_tables, bot: discord.ext.commands.Bot):
    message_id = (await dpytest.message("test_msg",bot.guilds[0].channels[0])).id
    sql_add_message = "INSERT INTO UserInTwitchAlert(channel_id, twitch_username, custom_message, message_id) " \
                      f"VALUES({bot.guilds[0].channels[0].id},'monstercat',Null,{message_id}) "
    twitch_alert_db_manager_tables.get_parent_database_manager().db_execute_commit(sql_add_message)
    await twitch_alert_db_manager_tables.delete_all_offline_streams(False, ['monstercat'])
    sql_select_messages = "SELECT message_id,twitch_username FROM UserInTwitchAlert " \
                          f"WHERE twitch_username = 'monstercat' AND channel_id = {bot.guilds[0].channels[0].id}"
    result = twitch_alert_db_manager_tables.get_parent_database_manager().db_execute_select(sql_select_messages)
    assert len(result) == 1
    assert result[0][0] is None
    with pytest.raises(discord.errors.NotFound,
                       match="Unknown Message"):
        await bot.guilds[0].channels[0].fetch_message(message_id)
    pass


@pytest.mark.asyncio()
async def test_delete_all_offline_streams_team(twitch_alert_db_manager_tables, bot: discord.ext.commands.Bot):
    await test_update_all_teams_members(twitch_alert_db_manager_tables)
    sql_add_message = "UPDATE UserInTwitchTeam SET message_id = 1 " \
                      "WHERE (team_twitch_alert_id = 614 OR team_twitch_alert_id = 616) " \
                      "AND twitch_username = 'monstercat'"
    twitch_alert_db_manager_tables.get_parent_database_manager().db_execute_commit(sql_add_message)
    await twitch_alert_db_manager_tables.delete_all_offline_streams(True, ['monstercat'])
    sql_select_messages = "SELECT message_id,twitch_username FROM UserInTwitchTeam " \
                          "WHERE (team_twitch_alert_id = 614 OR team_twitch_alert_id = 616) " \
                          "AND twitch_username = 'monstercat'"
    result = twitch_alert_db_manager_tables.get_parent_database_manager().db_execute_select(sql_select_messages)
    assert len(result) == 2
    assert result[0][0] is None
    assert result[1][0] is None
    pass
