#!/usr/bin/env python

"""
Testing KoalaBot twitch_alert

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

import discord
# Libs
import discord.ext.test as dpytest
import mock
import pytest
import pytest_asyncio
from discord.ext import commands
from sqlalchemy import select, update, insert, delete, and_, or_
from twitchAPI.object import Stream

from koala.cogs.twitch_alert import utils
# Own modules
from koala.cogs.twitch_alert.cog import TwitchAlert
from koala.cogs.twitch_alert.db import TwitchAlertDBManager
from koala.cogs.twitch_alert.models import TwitchAlerts, TeamInTwitchAlert, UserInTwitchTeam, UserInTwitchAlert
from koala.db import session_manager

# Constants
DB_PATH = "Koala.db"


# Variables

@pytest_asyncio.fixture
async def twitch_cog(bot: discord.ext.commands.Bot):
    """ setup any state specific to the execution of the given module."""
    twitch_cog = TwitchAlert(bot)
    await bot.add_cog(twitch_cog)
    await dpytest.empty_queue()
    dpytest.configure(bot)
    return twitch_cog


@pytest_asyncio.fixture
async def twitch_alert_db_manager(twitch_cog: TwitchAlert):
    twitch_alert_db_manager = TwitchAlertDBManager(twitch_cog.bot)
    await twitch_alert_db_manager.setup_twitch_handler()
    return twitch_alert_db_manager


@pytest.fixture(autouse=True)
def twitch_alert_db_manager_tables(twitch_alert_db_manager):
    with session_manager() as session:
        session.execute(delete(TwitchAlerts))
        session.execute(delete(TeamInTwitchAlert))
        session.execute(delete(UserInTwitchAlert))
        session.execute(delete(UserInTwitchTeam))
        session.commit()
        return twitch_alert_db_manager


def test_create_tables():
    tables = ['TwitchAlerts', 'UserInTwitchAlert', 'TeamInTwitchAlert', 'UserInTwitchTeam']
    sql_check_table_exists = "SELECT name FROM sqlite_master " \
                             "WHERE type='table' AND " \
                             "name IN ('TwitchAlerts', 'UserInTwitchAlert', 'TeamInTwitchAlert', 'UserInTwitchTeam');"
    with session_manager() as session:
        tables_found = session.execute(sql_check_table_exists).all()
    for table in tables_found:
        assert table.name in tables


def test_new_ta(twitch_alert_db_manager_tables):
    assert utils.DEFAULT_MESSAGE == twitch_alert_db_manager_tables.new_ta(guild_id=1234, channel_id=2345)

    sql_check_db_updated = select(TwitchAlerts.guild_id, TwitchAlerts.default_message)\
        .where(TwitchAlerts.channel_id == 2345)
    with session_manager() as session:
        result: TwitchAlerts = session.execute(sql_check_db_updated).fetchone()
    assert result.guild_id == 1234
    assert result.default_message == utils.DEFAULT_MESSAGE


def test_new_ta_message(twitch_alert_db_manager_tables):
    test_message = "Test message"
    assert test_message == twitch_alert_db_manager_tables.new_ta(guild_id=1234, channel_id=23456,
                                                                 default_message=test_message)

    sql_check_db_updated = select(TwitchAlerts.guild_id, TwitchAlerts.default_message)\
        .where(TwitchAlerts.channel_id == 23456)
    with session_manager() as session:
        result: TwitchAlerts = session.execute(sql_check_db_updated).fetchone()
    assert result.guild_id == 1234
    assert result.default_message == test_message


def test_new_ta_replace(twitch_alert_db_manager_tables):
    test_message = "Test message"
    test_new_ta_message(twitch_alert_db_manager_tables=twitch_alert_db_manager_tables)
    assert test_message == twitch_alert_db_manager_tables.new_ta(guild_id=1234, channel_id=23456,
                                                                 default_message=test_message, replace=True)

    sql_check_db_updated = select(TwitchAlerts.guild_id, TwitchAlerts.default_message)\
        .where(TwitchAlerts.channel_id == 23456)
    with session_manager() as session:
        result: TwitchAlerts = session.execute(sql_check_db_updated).fetchone()
    assert result.guild_id == 1234
    assert result.default_message == test_message


def test_add_user_to_ta_default_message(twitch_alert_db_manager_tables):
    twitch_alert_db_manager_tables.new_ta(1234, 1234567891, None)
    twitch_alert_db_manager_tables.add_user_to_ta(1234567891, "monstercat", None, 1234)

    sql_find_twitch_alert = select(UserInTwitchAlert.twitch_username, UserInTwitchAlert.custom_message)\
        .where(and_(UserInTwitchAlert.channel_id == 1234567891, UserInTwitchAlert.twitch_username == 'monstercat'))
    with session_manager() as session:
        result: TwitchAlerts = session.execute(sql_find_twitch_alert).fetchone()
    assert result.twitch_username == 'monstercat'
    assert result.custom_message is None


def test_add_user_to_ta_custom_message(twitch_alert_db_manager_tables):
    twitch_alert_db_manager_tables.new_ta(1234, 1234567892, None)
    twitch_alert_db_manager_tables.add_user_to_ta(1234567892, "monstercat", "FiddleSticks {user} is live!", 1234)

    sql_find_twitch_alert = select(UserInTwitchAlert.twitch_username, UserInTwitchAlert.custom_message)\
        .where(and_(UserInTwitchAlert.channel_id == 1234567892, UserInTwitchAlert.twitch_username == 'monstercat'))
    with session_manager() as session:
        result: TwitchAlerts = session.execute(sql_find_twitch_alert).fetchone()
    assert result.twitch_username == 'monstercat'
    assert result.custom_message == "FiddleSticks {user} is live!"


@pytest.mark.asyncio()
async def test_remove_user_from_ta(twitch_alert_db_manager_tables):
    test_add_user_to_ta_default_message(twitch_alert_db_manager_tables)
    await twitch_alert_db_manager_tables.remove_user_from_ta(1234567891, "monstercat")

    sql_find_twitch_alert = select(UserInTwitchAlert.twitch_username, UserInTwitchAlert.custom_message)\
        .where(and_(UserInTwitchAlert.channel_id == 1234567891, UserInTwitchAlert.twitch_username == 'monstercat'))
    with session_manager() as session:
        assert session.execute(sql_find_twitch_alert).one_or_none() is None


@pytest.mark.asyncio()
async def test_delete_message(twitch_alert_db_manager_tables):
    with mock.patch.object(discord.TextChannel, 'fetch_message') as mock1:
        await twitch_alert_db_manager_tables.delete_message(1234, dpytest.get_config().channels[0].id)
    mock1.assert_called_with(1234)


def test_add_team_to_ta(twitch_alert_db_manager_tables):
    twitch_alert_db_manager_tables.add_team_to_ta(channel_id=566, twitch_team="faze", custom_message=None, guild_id=568)

    sql_select_team = select(TeamInTwitchAlert.custom_message)\
        .where(and_(TeamInTwitchAlert.channel_id == 566, TeamInTwitchAlert.twitch_team_name == 'faze'))
    with session_manager() as session:
        result: TeamInTwitchAlert = session.execute(sql_select_team).fetchone()

    assert result.custom_message is None


def test_add_team_to_ta_custom_message(twitch_alert_db_manager_tables, channel_id=573, guild_id=574):
    twitch_alert_db_manager_tables.add_team_to_ta(channel_id=channel_id, twitch_team="faze",
                                                  custom_message="Message here", guild_id=guild_id)

    sql_select_team = select(TeamInTwitchAlert.custom_message)\
        .where(and_(TeamInTwitchAlert.channel_id == channel_id, TeamInTwitchAlert.twitch_team_name == 'faze'))
    with session_manager() as session:
        result: TeamInTwitchAlert = session.execute(sql_select_team).fetchone()

    assert result.custom_message == "Message here"


@pytest.mark.asyncio()
async def test_remove_team_from_ta(twitch_alert_db_manager_tables):
    test_add_team_to_ta_custom_message(twitch_alert_db_manager_tables, channel_id=590, guild_id=591)
    await twitch_alert_db_manager_tables.remove_team_from_ta(590, "faze")

    sql_select_team = select(TeamInTwitchAlert.custom_message)\
        .where(and_(TeamInTwitchAlert.channel_id == 590, TeamInTwitchAlert.twitch_team_name == 'faze'))
    with session_manager() as session:
        assert session.execute(sql_select_team).one_or_none() is None


@pytest.mark.asyncio()
async def test_remove_team_from_ta_duplicate(twitch_alert_db_manager_tables):
    test_add_team_to_ta_custom_message(twitch_alert_db_manager_tables, channel_id=590, guild_id=591)
    test_add_team_to_ta_custom_message(twitch_alert_db_manager_tables, channel_id=590, guild_id=591)
    await twitch_alert_db_manager_tables.remove_team_from_ta(590, "faze")

    sql_select_team = select(TeamInTwitchAlert.custom_message)\
        .where(and_(TeamInTwitchAlert.channel_id == 590, TeamInTwitchAlert.twitch_team_name == 'faze'))
    with session_manager() as session:
        assert session.execute(sql_select_team).one_or_none() is not None


@pytest.mark.asyncio()
async def test_remove_team_from_ta_invalid(twitch_alert_db_manager_tables):
    with pytest.raises(AttributeError,
                       match="Team name not found"):
        await twitch_alert_db_manager_tables.remove_team_from_ta(590, 590)


@pytest.mark.asyncio()
async def test_remove_team_from_ta_deletes_messages(twitch_alert_db_manager_tables):
    await test_update_team_members(twitch_alert_db_manager_tables)

    test = update(UserInTwitchTeam)\
        .where(and_(UserInTwitchTeam.team_twitch_alert_id == 604,
                    UserInTwitchTeam.twitch_username == 'monstercat')).values(message_id=1)
    with session_manager() as session:
        session.execute(test)
        session.commit()

    with mock.patch.object(TwitchAlertDBManager, 'delete_message') as mock1:
        await twitch_alert_db_manager_tables.remove_team_from_ta(605, "monstercat")
    mock1.assert_called_with(1, 605)


@pytest.mark.asyncio()
async def test_update_team_members(twitch_alert_db_manager_tables):
    sql_insert_monstercat_team = insert(TeamInTwitchAlert).values(
        team_twitch_alert_id=604, channel_id=605, twitch_team_name='monstercat')
    with session_manager() as session:
        session.execute(sql_insert_monstercat_team)
        session.commit()

        await twitch_alert_db_manager_tables.update_team_members(604, "monstercat")

        sql_select_monstercat_team = select(UserInTwitchTeam).where(and_(UserInTwitchTeam.team_twitch_alert_id == 604,
                                                                         UserInTwitchTeam.twitch_username == 'monstercat'))

        result = session.execute(sql_select_monstercat_team)
        assert result.one_or_none() is not None


@pytest.mark.asyncio()
async def test_update_all_teams_members(twitch_alert_db_manager_tables):
    sql_insert_monstercat_team = insert(TeamInTwitchAlert).values(
        team_twitch_alert_id=614, channel_id=615, twitch_team_name='monstercat')
    with session_manager() as session:
        session.execute(sql_insert_monstercat_team)

        sql_insert_monstercat_team = insert(TeamInTwitchAlert).values(
            team_twitch_alert_id=616, channel_id=617, twitch_team_name='monstercat')
        session.execute(sql_insert_monstercat_team)
        session.commit()

        await twitch_alert_db_manager_tables.update_all_teams_members()

        sql_select_monstercats_team = select(UserInTwitchTeam.twitch_username).where(and_(
                or_(UserInTwitchTeam.team_twitch_alert_id == 614, UserInTwitchTeam.team_twitch_alert_id == 616),
                UserInTwitchTeam.twitch_username == 'monstercat'))

        result = session.execute(sql_select_monstercats_team).all()
        assert len(result) == 2


@pytest.mark.asyncio()
async def test_delete_all_offline_streams(twitch_alert_db_manager_tables, bot: discord.ext.commands.Bot):
    message_id = (await dpytest.message("test_msg", bot.guilds[0].channels[0])).id
    sql_add_message = insert(UserInTwitchAlert).values(
        channel_id=bot.guilds[0].channels[0].id,
        twitch_username='monstercat',
        custom_message=None,
        message_id=message_id)
    with session_manager() as session:
        session.execute(sql_add_message)
        session.commit()

        await twitch_alert_db_manager_tables.delete_all_offline_streams(['monstercat'])

        sql_select_messages = select(UserInTwitchAlert).where(and_(
            UserInTwitchAlert.twitch_username == 'monstercat',
            UserInTwitchAlert.channel_id == bot.guilds[0].channels[0].id))
        result = session.execute(sql_select_messages).scalars().one_or_none()

        assert result is not None
        assert result.message_id is None
        with pytest.raises(discord.errors.NotFound,
                           match="Unknown Message"):
            await bot.guilds[0].channels[0].fetch_message(message_id)


@pytest.mark.asyncio()
async def test_delete_all_offline_streams_team(twitch_alert_db_manager_tables, bot: discord.ext.commands.Bot):
    await test_update_all_teams_members(twitch_alert_db_manager_tables)

    sql_add_message = update(UserInTwitchTeam).where(and_(or_(
        UserInTwitchTeam.team_twitch_alert_id == 614, UserInTwitchTeam.team_twitch_alert_id == 616),
        UserInTwitchTeam.twitch_username == 'monstercat')).values(message_id=1)
    with session_manager() as session:
        session.execute(sql_add_message)
        session.commit()

        await twitch_alert_db_manager_tables.delete_all_offline_team_streams(['monstercat'])

        sql_select_messages = select(UserInTwitchTeam.message_id, UserInTwitchTeam.twitch_username).where(
            and_(or_(UserInTwitchTeam.team_twitch_alert_id == 614, UserInTwitchTeam.team_twitch_alert_id == 616),
                 UserInTwitchTeam.twitch_username == 'monstercat'))
        result = session.execute(sql_select_messages).fetchall()

        assert len(result) == 2
        assert result[0].message_id is None
        assert result[1].message_id is None


@pytest.mark.asyncio
async def test_create_alert_embed(twitch_alert_db_manager_tables):
    stream_data = Stream(id='3215560150671170227', user_id='27446517', user_name="Monstercat", user_login="monstercat",
                         game_id="26936", type='live', title='Music 24/7')

    assert type(await twitch_alert_db_manager_tables.create_alert_embed(stream_data, None)) is discord.Embed
