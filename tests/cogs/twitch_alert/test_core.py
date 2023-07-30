import asyncio

import discord
import discord.ext.test as dpytest
import pytest
import pytest_asyncio
from mock import mock
from sqlalchemy import select, and_, update, insert, or_, delete
from twitchAPI.object import Stream

from koala.cogs import TwitchAlert
from koala.cogs.twitch_alert import core, utils
from koala.cogs.twitch_alert.db import TwitchAlertDBManager
from koala.cogs.twitch_alert.env import TWITCH_KEY, TWITCH_SECRET
from koala.cogs.twitch_alert.models import TeamInTwitchAlert, TwitchAlerts, UserInTwitchAlert, UserInTwitchTeam
from koala.db import setup


@pytest_asyncio.fixture
async def twitch_cog(bot: discord.ext.commands.Bot):
    """ setup any state specific to the execution of the given module."""
    twitch_cog = TwitchAlert(bot)
    await bot.add_cog(twitch_cog)
    await dpytest.empty_queue()
    dpytest.configure(bot)
    return twitch_cog


@pytest.fixture(scope="session", autouse=True)
def setup_twitch_handler():
    asyncio.get_event_loop().run_until_complete(core.twitch_handler.setup(TWITCH_KEY, TWITCH_SECRET))


@pytest.fixture(scope="function", autouse=True)
def twitch_alert_db_manager_tables(session):
    session.execute(delete(TwitchAlerts))
    session.execute(delete(TeamInTwitchAlert))
    session.execute(delete(UserInTwitchAlert))
    session.execute(delete(UserInTwitchTeam))
    session.commit()

    setup()


def test_new_ta(session):
    assert utils.DEFAULT_MESSAGE == core.new_ta(guild_id=1234, channel_id=2345, session=session)

    sql_check_db_updated = select(TwitchAlerts.guild_id, TwitchAlerts.default_message) \
        .where(TwitchAlerts.channel_id == 2345)
    result: TwitchAlerts = session.execute(sql_check_db_updated).fetchone()
    assert result.guild_id == 1234
    assert result.default_message == utils.DEFAULT_MESSAGE


def test_add_team_to_ta_custom_message(session, channel_id=573, guild_id=574):
    core.add_team_to_ta(channel_id=channel_id, twitch_team="faze",
                        custom_message="Message here", guild_id=guild_id)

    sql_select_team = select(TeamInTwitchAlert.custom_message) \
        .where(and_(TeamInTwitchAlert.channel_id == channel_id, TeamInTwitchAlert.twitch_team_name == 'faze'))
    result: TeamInTwitchAlert = session.execute(sql_select_team).fetchone()

    assert result.custom_message == "Message here"


@pytest.mark.asyncio()
async def test_remove_team_from_ta_duplicate(bot, session):
    test_add_team_to_ta_custom_message(session, channel_id=590, guild_id=591)
    test_add_team_to_ta_custom_message(session, channel_id=590, guild_id=591)
    await core.remove_team_from_ta(bot, 590, "faze", session=session)

    sql_select_team = select(TeamInTwitchAlert.custom_message) \
        .where(and_(TeamInTwitchAlert.channel_id == 590, TeamInTwitchAlert.twitch_team_name == 'faze'))
    assert session.execute(sql_select_team).one_or_none() is not None


@pytest.mark.asyncio()
async def test_remove_team_from_ta(bot, session):
    test_add_team_to_ta_custom_message(session, channel_id=590, guild_id=591)
    await core.remove_team_from_ta(bot, 590, "faze", session=session)

    sql_select_team = select(TeamInTwitchAlert.custom_message) \
        .where(and_(TeamInTwitchAlert.channel_id == 590, TeamInTwitchAlert.twitch_team_name == 'faze'))
    assert session.execute(sql_select_team).one_or_none() is None


def test_new_ta_message(session):
    test_message = "Test message"
    assert test_message == core.new_ta(guild_id=1234, channel_id=23456,
                                       default_message=test_message, session=session)

    sql_check_db_updated = select(TwitchAlerts.guild_id, TwitchAlerts.default_message) \
        .where(TwitchAlerts.channel_id == 23456)
    result: TwitchAlerts = session.execute(sql_check_db_updated).fetchone()
    assert result.guild_id == 1234
    assert result.default_message == test_message


def test_new_ta_replace(session):
    test_message = "Test message"
    test_new_ta_message(session=session)
    assert test_message == core.new_ta(guild_id=1234, channel_id=23456,
                                       default_message=test_message, replace=True, session=session)

    sql_check_db_updated = select(TwitchAlerts.guild_id, TwitchAlerts.default_message) \
        .where(TwitchAlerts.channel_id == 23456)
    result: TwitchAlerts = session.execute(sql_check_db_updated).fetchone()
    assert result.guild_id == 1234
    assert result.default_message == test_message


def test_add_user_to_ta_default_message(session):
    core.new_ta(1234, 1234567891, None, session=session)
    core.add_user_to_ta(1234567891, "monstercat", None, 1234, session=session)

    sql_find_twitch_alert = select(UserInTwitchAlert.twitch_username, UserInTwitchAlert.custom_message) \
        .where(and_(UserInTwitchAlert.channel_id == 1234567891, UserInTwitchAlert.twitch_username == 'monstercat'))
    result: TwitchAlerts = session.execute(sql_find_twitch_alert).fetchone()
    assert result.twitch_username == 'monstercat'
    assert result.custom_message is None


def test_add_user_to_ta_custom_message(session):
    core.new_ta(1234, 1234567892, None, session=session)
    core.add_user_to_ta(1234567892, "monstercat", "FiddleSticks {user} is live!", 1234)

    sql_find_twitch_alert = select(UserInTwitchAlert.twitch_username, UserInTwitchAlert.custom_message) \
        .where(and_(UserInTwitchAlert.channel_id == 1234567892, UserInTwitchAlert.twitch_username == 'monstercat'))
    result: TwitchAlerts = session.execute(sql_find_twitch_alert).fetchone()
    assert result.twitch_username == 'monstercat'
    assert result.custom_message == "FiddleSticks {user} is live!"


@pytest.mark.asyncio()
async def test_remove_user_from_ta(bot, session):
    test_add_user_to_ta_default_message(session=session)
    await core.remove_user_from_ta(bot, 1234567891, "monstercat")

    sql_find_twitch_alert = select(UserInTwitchAlert.twitch_username, UserInTwitchAlert.custom_message) \
        .where(and_(UserInTwitchAlert.channel_id == 1234567891, UserInTwitchAlert.twitch_username == 'monstercat'))
    assert session.execute(sql_find_twitch_alert).one_or_none() is None


def test_add_team_to_ta(session):
    core.add_team_to_ta(channel_id=566, twitch_team="faze", custom_message=None, guild_id=568, session=session)

    sql_select_team = select(TeamInTwitchAlert.custom_message) \
        .where(and_(TeamInTwitchAlert.channel_id == 566, TeamInTwitchAlert.twitch_team_name == 'faze'))
    result: TeamInTwitchAlert = session.execute(sql_select_team).fetchone()

    assert result.custom_message is None


@pytest.mark.asyncio()
async def test_remove_team_from_ta_invalid(bot, session):
    with pytest.raises(AttributeError,
                       match="Team name not found"):
        await core.remove_team_from_ta(bot, 590, 590, session=session)


@pytest.mark.asyncio()
async def test_update_team_members(session):
    sql_insert_monstercat_team = insert(TeamInTwitchAlert).values(
        team_twitch_alert_id=604, channel_id=605, twitch_team_name='monstercat')
    session.execute(sql_insert_monstercat_team)
    session.commit()

    await core.update_team_members(604, "monstercat", session=session)

    sql_select_monstercat_team = select(UserInTwitchTeam).where(and_(UserInTwitchTeam.team_twitch_alert_id == 604,
                                                                     UserInTwitchTeam.twitch_username == 'monstercat'))

    result = session.execute(sql_select_monstercat_team)
    assert result.one_or_none() is not None


@pytest.mark.asyncio()
async def test_remove_team_from_ta_deletes_messages(bot, session):
    await test_update_team_members(session)

    test = update(UserInTwitchTeam) \
        .where(and_(UserInTwitchTeam.team_twitch_alert_id == 604,
                    UserInTwitchTeam.twitch_username == 'monstercat')).values(message_id=1)
    session.execute(test)
    session.commit()

    with mock.patch("koala.cogs.twitch_alert.core.delete_message") as mock1:
        await core.remove_team_from_ta(bot, 605, "monstercat", session=session)
        mock1.assert_called_with(bot, 1, 605, session=session)


@pytest.mark.asyncio()
async def test_update_all_teams_members(session):
    sql_insert_monstercat_team = insert(TeamInTwitchAlert).values(
        team_twitch_alert_id=614, channel_id=615, twitch_team_name='monstercat')
    session.execute(sql_insert_monstercat_team)

    sql_insert_monstercat_team = insert(TeamInTwitchAlert).values(
        team_twitch_alert_id=616, channel_id=617, twitch_team_name='monstercat')
    session.execute(sql_insert_monstercat_team)
    session.commit()

    await core.update_all_teams_members(session=session)

    sql_select_monstercats_team = select(UserInTwitchTeam.twitch_username).where(and_(
        or_(UserInTwitchTeam.team_twitch_alert_id == 614, UserInTwitchTeam.team_twitch_alert_id == 616),
        UserInTwitchTeam.twitch_username == 'monstercat'))

    result = session.execute(sql_select_monstercats_team).all()
    assert len(result) == 2


@pytest.mark.asyncio()
async def test_delete_all_offline_streams_team(bot: discord.ext.commands.Bot, session):
    await test_update_all_teams_members(session)

    sql_add_message = update(UserInTwitchTeam).where(and_(or_(
        UserInTwitchTeam.team_twitch_alert_id == 614, UserInTwitchTeam.team_twitch_alert_id == 616),
        UserInTwitchTeam.twitch_username == 'monstercat')).values(message_id=1)
    session.execute(sql_add_message)
    session.commit()

    await core.delete_all_offline_team_streams(bot, ['monstercat'], session=session)

    sql_select_messages = select(UserInTwitchTeam.message_id, UserInTwitchTeam.twitch_username).where(
        and_(or_(UserInTwitchTeam.team_twitch_alert_id == 614, UserInTwitchTeam.team_twitch_alert_id == 616),
             UserInTwitchTeam.twitch_username == 'monstercat'))
    result = session.execute(sql_select_messages).fetchall()

    assert len(result) == 2
    assert result[0].message_id is None
    assert result[1].message_id is None


def test_create_tables(session):
    setup()
    tables = ['TwitchAlerts', 'UserInTwitchAlert', 'TeamInTwitchAlert', 'UserInTwitchTeam']
    sql_check_table_exists = "SELECT name FROM sqlite_master " \
                             "WHERE type='table' AND " \
                             "name IN ('TwitchAlerts', 'UserInTwitchAlert', 'TeamInTwitchAlert', 'UserInTwitchTeam');"
    tables_found = session.execute(sql_check_table_exists).all()
    for table in tables_found:
        assert table.name in tables


@pytest.mark.asyncio()
async def test_delete_message(bot, session):
    with mock.patch.object(discord.TextChannel, 'fetch_message') as mock1:
        await core.delete_message(bot, 1234, dpytest.get_config().channels[0].id, session=session)
    mock1.assert_called_with(1234)


@pytest.mark.asyncio()
async def test_delete_all_offline_streams(bot: discord.ext.commands.Bot, session):
    message_id = (await dpytest.message("test_msg", bot.guilds[0].channels[0])).id
    sql_add_message = insert(UserInTwitchAlert).values(
        channel_id=bot.guilds[0].channels[0].id,
        twitch_username='monstercat',
        custom_message=None,
        message_id=message_id)
    session.execute(sql_add_message)
    session.commit()

    await core.delete_all_offline_streams(bot, ['monstercat'], session=session)

    sql_select_messages = select(UserInTwitchAlert).where(and_(
        UserInTwitchAlert.twitch_username == 'monstercat',
        UserInTwitchAlert.channel_id == bot.guilds[0].channels[0].id))
    result = session.execute(sql_select_messages).scalars().one_or_none()

    assert result is not None
    assert result.message_id is None
    with pytest.raises(discord.errors.NotFound,
                       match="Unknown Message"):
        await bot.guilds[0].channels[0].fetch_message(message_id)


@pytest.mark.asyncio
async def test_create_alert_embed():
    stream_data = Stream(id='3215560150671170227', user_id='27446517', user_name="Monstercat", user_login="monstercat",
                         game_id="26936", type='live', title='Music 24/7')

    assert type(await core.create_alert_embed(stream_data, None)) is discord.Embed
