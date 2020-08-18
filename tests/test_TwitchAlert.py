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
        os.remove(DB_PATH)
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
    stream_info = {'user_name': "Test", 'title': "Test Title"}
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
    stream_info = {'user_name': "Test", 'title': "Test Title"}
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
async def twitch_cog():
    """ setup any state specific to the execution of the given module."""
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    database_manager = KoalaDBManager.KoalaDBManager(DB_PATH)
    twitch_cog = TwitchAlert.TwitchAlert(bot, database_manager=database_manager)
    bot.add_cog(twitch_cog)
    await dpytest.empty_queue()
    dpytest.configure(bot)
    print("Tests starting")
    return twitch_cog


@mock.patch("utils.KoalaUtils.random_id", mock.MagicMock(return_value=7357))
@pytest.mark.asyncio(order=1)
async def test_edit_default_message_default_from_none(twitch_cog):
    this_channel = dpytest.get_config().channels[0]
    KoalaBot.database_manager.db_execute_commit(f"DELETE FROM TwitchAlerts WHERE channel_id={this_channel.id}")
    assert_embed = discord.Embed(title="Default Message Edited",
                                 description=f"Guild: {dpytest.get_config().guilds[0].id}\n"
                                             f"Channel: {this_channel.id}\n"
                                             f"Default Message: {TwitchAlert.DEFAULT_MESSAGE}")

    await dpytest.message(KoalaBot.COMMAND_PREFIX + f"edit_default_message {this_channel.id}")
    dpytest.verify_embed(embed=assert_embed)
    sql_check_db_updated = f"SELECT * FROM TwitchAlerts WHERE channel_id = {this_channel.id}"
    assert KoalaBot.database_manager.db_execute_select(sql_check_db_updated) is not None


@mock.patch("utils.KoalaUtils.random_id", mock.MagicMock(return_value=7357))
@pytest.mark.asyncio(order=2)
async def test_edit_default_message_existing(twitch_cog):
    this_channel = dpytest.get_config().channels[0]
    sql_add_twitch_alert = f"INSERT INTO TwitchAlerts(guild_id, channel_id, default_message) " \
                           f"VALUES {dpytest.get_config().guilds[0].id}, {this_channel.id}," \
                           "'{user} is good'"
    KoalaBot.database_manager.db_execute_commit(sql_add_twitch_alert)
    assert_embed = discord.Embed(title="Default Message Edited",
                                 description=f"Guild: {dpytest.get_config().guilds[0].id}\n"
                                             f"Channel: {this_channel.id}\n"
                                             "Default Message: {user} is bad")

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "edit_default_message " + str(this_channel.id) + " {user} is bad")
    dpytest.verify_embed(embed=assert_embed)
    sql_check_db_updated = f"SELECT * FROM TwitchAlerts WHERE channel_id = {this_channel.id}"
    assert KoalaBot.database_manager.db_execute_select(sql_check_db_updated) is not None


@pytest.mark.asyncio(order=3)
async def test_add_user_to_twitch_alert(twitch_cog):
    assert_embed = discord.Embed(title="Added User to Twitch Alert",
                                 description=f"Channel: {dpytest.get_config().channels[0].id}\n"
                                             f"User: monstercat\n"
                                             f"Message: {TwitchAlert.DEFAULT_MESSAGE}",
                                 colour=KOALA_GREEN)

    await dpytest.message(
        f"{KoalaBot.COMMAND_PREFIX}add_user_to_twitch_alert {dpytest.get_config().channels[0].id} monstercat")
    dpytest.verify_embed(embed=assert_embed)


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
    dpytest.verify_embed(
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
    dpytest.verify_embed(embed=assert_embed)

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
    dpytest.verify_embed(new_embed)
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
    dpytest.verify_embed(
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
    dpytest.verify_embed(assert_embed)


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
    dpytest.verify_embed(assert_embed)


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
    dpytest.verify_embed(
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
    dpytest.verify_embed(new_embed)
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
    dpytest.verify_embed(
        embed=TwitchAlert.error_embed("The channel ID provided is either invalid, or not in this server."))


@pytest.mark.asyncio()
async def test_on_ready(twitch_cog):
    with mock.patch.object(TwitchAlert.TwitchAlert, 'start_loop') as mock1:
        await twitch_cog.on_ready()
    mock1.assert_called_with()


def test_start_loop(twitch_cog):
    with mock.patch.object(TwitchAlert.TwitchAlert, 'loop_check_live') as mock1:
        twitch_cog.start_loop()
    mock1.assert_called_with()
    assert twitch_cog.loop_thread is not None


def test_start_loop_repeated(twitch_cog):
    twitch_cog.start_loop()
    with pytest.raises(Exception,
                       match="Loop is already running!"):
        twitch_cog.start_loop()


def test_end_loop(twitch_cog):
    twitch_cog.start_loop()
    assert twitch_cog.loop_thread is not None

    twitch_cog.end_loop()
    assert twitch_cog.loop_thread is None


def test_end_empty_loop(twitch_cog):
    with pytest.raises(Exception,
                       match="Loop is not running!"):
        twitch_cog.end_loop()


@mock.patch("utils.KoalaUtils.random_id", mock.MagicMock(return_value=7363))
@mock.patch("cogs.TwitchAlert.TwitchAPIHandler.get_streams_data",
            mock.MagicMock(return_value={'id': '3215560150671170227', 'user_id': '27446517',
                                         "user_name": "Monstercat", 'game_id': "26936", 'type': 'live',
                                         'title': 'Music 24/7'}))
@pytest.mark.skip(reason="Issues with testing inside asyncio event loop")
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
    dpytest.verify_embed(expected_embed)


# Test TwitchAPIHandler

@pytest.fixture
def twitch_api_handler():
    return TwitchAlert.TwitchAPIHandler(TwitchAlert.TWITCH_CLIENT_ID, TwitchAlert.TWITCH_SECRET)


def test_get_new_twitch_oauth(twitch_api_handler):
    assert twitch_api_handler.get_new_twitch_oauth()


def test_requests_get(twitch_api_handler):
    assert twitch_api_handler.requests_get("https://api.twitch.tv/helix/streams?",
                                           params=(('user_login', 'monstercat'),)).json().get("data") is not None


def test_requests_get_kraken(twitch_api_handler):
    # When Twitch API v5 becomes depreciated this will no longer function
    assert twitch_api_handler.requests_get("https://api.twitch.tv/kraken/teams/uosvge",
                                           headers={'Client-ID': TwitchAlert.TWITCH_CLIENT_ID,
                                                    'Accept': 'application/vnd.twitchtv.v5+json'}
                                           ).json().get("users") is not None


def test_get_streams_data(twitch_api_handler):
    usernames = ['monstercat', 'jaydwee']
    print(twitch_api_handler.get_streams_data(usernames))
    assert twitch_api_handler.get_streams_data(usernames) is not None


def test_get_user_data(twitch_api_handler):
    assert twitch_api_handler.get_user_data('monstercat') is not None


def test_get_game_data(twitch_api_handler):
    assert twitch_api_handler.get_game_data('26936').get('name') == 'Music & Performing Arts'


def test_get_team_users(twitch_api_handler):
    # assumes uosvge is in the team called uosvge
    members = twitch_api_handler.get_team_users('uosvge')
    for member in members:
        if member.get('name') == 'uosvge':
            assert True
            return
    assert False


# Test TwitchAlertDBManager
@pytest.fixture
def twitch_alert_db_manager(twitch_cog):
    return TwitchAlert.TwitchAlertDBManager(KoalaDBManager.KoalaDBManager(DB_PATH), twitch_cog.bot)


@pytest.fixture
def twitch_alert_db_manager_tables(twitch_cog):
    twitch_alert_db_manager = TwitchAlert.TwitchAlertDBManager(KoalaDBManager.KoalaDBManager(DB_PATH), twitch_cog.bot)
    twitch_alert_db_manager.create_tables()
    return twitch_alert_db_manager


def test_get_parent_database_manager(twitch_alert_db_manager):
    assert type(twitch_alert_db_manager.get_parent_database_manager()) is KoalaDBManager.KoalaDBManager


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


def test_remove_user_from_ta(twitch_alert_db_manager_tables):
    test_add_user_to_ta_default_message(twitch_alert_db_manager_tables)
    twitch_alert_db_manager_tables.remove_user_from_ta(1234567891, "monstercat")
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

def test_sql_create_ta_not_exists():
    pass





def test_update_team_members():
    pass


def test_update_all_teams_members():
    pass
