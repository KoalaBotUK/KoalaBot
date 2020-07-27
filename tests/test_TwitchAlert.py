#!/usr/bin/env python

"""
Testing KoalaBot TwitchAlert

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import os
import time

# Libs
import discord.ext.test as dpytest
import mock
import pytest
import discord
from discord.ext import commands

# Own modules
import KoalaBot
from cogs import TwitchAlert
from utils import KoalaDBManager

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
    expected = discord.Embed(colour=KoalaBot.KOALA_GREEN,
                             title="<:twitch:734024383957434489>  Test is now streaming!",
                             description="https://twitch.tv/test")
    expected.add_field(name="Stream Title", value="Test Title")
    expected.add_field(name="Playing", value="TestGame")
    expected.set_thumbnail(url="http://koalabot.uk")

    # Create JSON required to pass to method
    stream_info = {'user_name': "Test", 'title': "Test Title"}
    user_info = {'profile_image_url': "http://koalabot.uk"}
    game_info = {'name': "TestGame"}

    # Get response and assert equal
    result = TwitchAlert.create_live_embed(stream_info, user_info, game_info)
    assert dpytest.embed_eq(result, expected)


@pytest.mark.asyncio
async def test_setup():
    with mock.patch.object(discord.ext.commands.bot.Bot, 'add_cog') as mock1:
        TwitchAlert.setup(KoalaBot.client)
    mock1.assert_called()


# Test TwitchAlert

@pytest.fixture
def twitch_cog():
    """ setup any state specific to the execution of the given module."""
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    twitch_cog = TwitchAlert.TwitchAlert(bot)
    bot.add_cog(twitch_cog)
    dpytest.configure(bot)
    print("Tests starting")
    return twitch_cog


@mock.patch("utils.KoalaUtils.random_id", mock.MagicMock(return_value=7357))
@pytest.mark.asyncio(order=1)
async def test_create_twitch_alert_no_message(twitch_cog):
    KoalaBot.database_manager.db_execute_commit("DELETE FROM TwitchAlerts WHERE twitch_alert_id=7357")
    assert_embed = discord.Embed(title="New Twitch Alert Created!")
    assert_embed.set_footer(text="Twitch Alert ID: 7357")

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "create_twitch_alert ")
    dpytest.verify_embed(embed=assert_embed)


@mock.patch("utils.KoalaUtils.random_id", mock.MagicMock(return_value=7358))
@pytest.mark.asyncio(order=1)
async def test_create_twitch_alert_with_message(twitch_cog):
    KoalaBot.database_manager.db_execute_commit("DELETE FROM TwitchAlerts WHERE twitch_alert_id=7358")
    assert_embed = discord.Embed(title="New Twitch Alert Created!")
    assert_embed.set_footer(text="Twitch Alert ID: 7358")

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "create_twitch_alert {user} is live! {url}")
    dpytest.verify_embed(embed=assert_embed)


@pytest.mark.asyncio(order=2)
async def test_add_twitch_alert_to_channel(twitch_cog):
    this_channel = dpytest.get_config().channels[0]
    assert_embed = discord.Embed(title="Added to Channel",
                                 description=f"channel ID {this_channel.id} Added to Twitch Alert!")
    assert_embed.set_footer(text="Twitch Alert ID: 7358")

    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}add_twitch_alert_to_channel 7358 {this_channel.id}")
    dpytest.verify_embed(embed=assert_embed)


@pytest.mark.asyncio(order=2)
async def test_add_user_to_twitch_alert(twitch_cog):
    assert_embed = discord.Embed(title="Added User to Twitch Alert")
    assert_embed.set_footer(text="Twitch Alert ID: 7358")

    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}add_user_to_twitch_alert 7358 monstercat")
    dpytest.verify_embed(embed=assert_embed)


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


@mock.patch("utils.KoalaUtils.random_id", mock.MagicMock(return_value=7362))
@pytest.mark.asyncio
async def test_loop_check_live(twitch_cog):
    this_channel = dpytest.get_config().channels[0]
    expected_embed = discord.Embed(colour=KoalaBot.KOALA_GREEN,
                             title="<:twitch:734024383957434489>  Monstercat is now streaming!",
                             description="https://twitch.tv/monstercat")
    expected_embed.add_field(name="Stream Title", value="Non Stop Music - Monstercat Radio :notes:")
    expected_embed.add_field(name="Playing", value="Music & Performing Arts")
    expected_embed.set_thumbnail(url="https://static-cdn.jtvnw.net/jtv_user_pictures/monstercat-profile_image-3e109d75f8413319-300x300.jpeg")

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "create_twitch_alert")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}add_twitch_alert_to_channel 7362 {this_channel.id}")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}add_user_to_twitch_alert 7362 monstercat")
    twitch_cog.start_loop()
    time.sleep(2)
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


def test_get_streams_data(twitch_api_handler):
    usernames = ['monstercat', 'jaydwee']
    print(twitch_api_handler.get_streams_data(usernames))
    assert twitch_api_handler.get_streams_data(usernames) is not None


def test_get_user_data(twitch_api_handler):
    assert twitch_api_handler.get_user_data('monstercat') is not None


def test_get_game_data(twitch_api_handler):
    assert twitch_api_handler.get_game_data('26936').get('name') == 'Music & Performing Arts'


# Test TwitchAlertDBManager
@pytest.fixture
def twitch_alert_db_manager():
    return TwitchAlert.TwitchAlertDBManager(KoalaDBManager.KoalaDBManager(DB_PATH))


def test_before_create_tables(twitch_alert_db_manager):
    parent_database_manager = twitch_alert_db_manager.get_parent_database_manager()
    sql_check_table_exists = """SELECT name FROM sqlite_master WHERE type='table' AND name='TwitchAlerts';"""
    assert parent_database_manager.db_execute_select(sql_check_table_exists) == []


def test_create_tables(twitch_alert_db_manager):
    parent_database_manager = twitch_alert_db_manager.get_parent_database_manager()
    twitch_alert_db_manager.create_tables()
    for table in ["TwitchAlerts", "TwitchAlertInChannel", "UserInTwitchAlert",
                  "TeamInTwitchAlert", "UserInTwitchTeam", "TwitchDisplayInChannel"]:
        sql_check_table_exists = f"""SELECT name FROM sqlite_master WHERE type='table' AND name={table};"""
        assert parent_database_manager.db_execute_select(sql_check_table_exists) != []


def test_create_new_ta_default_message_none(twitch_alert_db_manager):
    twitch_alert_db_manager.create_tables()
    new_twitch_alert_id = twitch_alert_db_manager.create_new_ta(123456789, None)
    parent_database_manager = twitch_alert_db_manager.get_parent_database_manager()
    sql_find_twitch_alert = f"""SELECT guild_id, default_message 
                                FROM TwitchAlerts 
                                WHERE twitch_alert_id = {new_twitch_alert_id}"""
    result = parent_database_manager.db_execute_select(sql_find_twitch_alert)
    assert result[0][0] == 123456789
    assert result[0][1] == TwitchAlert.DEFAULT_MESSAGE


def test_add_ta_to_channel(twitch_alert_db_manager):
    twitch_alert_db_manager.create_tables()
    new_twitch_alert_id = twitch_alert_db_manager.create_new_ta(1234567891, None)
    twitch_alert_db_manager.add_ta_to_channel(new_twitch_alert_id, 2345)
    parent_database_manager = twitch_alert_db_manager.get_parent_database_manager()
    sql_find_twitch_alert = f"""SELECT channel_id 
                                FROM TwitchAlertInChannel 
                                WHERE twitch_alert_id = {new_twitch_alert_id}"""
    result = parent_database_manager.db_execute_select(sql_find_twitch_alert)
    assert result[0][0] == 2345


def test_add_user_to_ta_default_message(twitch_alert_db_manager):
    twitch_alert_db_manager.create_tables()
    new_twitch_alert_id = twitch_alert_db_manager.create_new_ta(1234567891, None)
    twitch_alert_db_manager.add_user_to_ta(new_twitch_alert_id, "monstercat", None)
    parent_database_manager = twitch_alert_db_manager.get_parent_database_manager()
    sql_find_twitch_alert = f"""SELECT twitch_username, custom_message
                                FROM UserInTwitchAlert
                                WHERE twitch_alert_id = {new_twitch_alert_id}"""
    result = parent_database_manager.db_execute_select(sql_find_twitch_alert)
    assert result[0][0] == "monstercat"
    assert result[0][1] is None


def test_add_user_to_ta_custom_message(twitch_alert_db_manager):
    twitch_alert_db_manager.create_tables()
    new_twitch_alert_id = twitch_alert_db_manager.create_new_ta(1234567891, None)
    twitch_alert_db_manager.add_user_to_ta(new_twitch_alert_id, "monstercat", "FiddleSticks {user} is live!")
    parent_database_manager = twitch_alert_db_manager.get_parent_database_manager()
    sql_find_twitch_alert = f"""SELECT twitch_username, custom_message
                                FROM UserInTwitchAlert
                                WHERE twitch_alert_id = {new_twitch_alert_id}"""
    result = parent_database_manager.db_execute_select(sql_find_twitch_alert)
    assert result[0][0] == "monstercat"
    assert result[0][1] == "FiddleSticks {user} is live!"
