#!/usr/bin/env python
# TODO Test rig broken, restart from beginning and fix.
"""
Testing KoalaBot IntroCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import asyncio
import threading

import discord.ext.commands.errors as discorderrors
import discord.ext.test as dpytest
import pytest
from discord.ext import commands
import discord
# Own modules
import KoalaBot
from cogs import IntroCog
from utils.KoalaDBManager import KoalaDBManager

# Constants

# Variables
intro_cog = None
DBManager = KoalaDBManager("./" + KoalaBot.DATABASE_PATH)
DBManager.create_base_tables()


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global intro_cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    intro_cog = IntroCog.IntroCog(bot)
    bot.add_cog(intro_cog)
    dpytest.configure(bot)
    print("Tests starting")


@pytest.mark.asyncio
async def test_on_guild_join():
    test_config = dpytest.get_config()
    client = test_config.client
    guild = dpytest.back.make_guild('TestGuildJoin', id_num=420)
    test_config.guilds.append(guild)
    await dpytest.member_join(1, client.user)
    await asyncio.sleep(0.5)
    # Try testing guild join on startup
    rows = DBManager.db_execute_select(
        f"""SELECT * FROM GuildWelcomeMessages WHERE guild_id = {guild.id};""")

    if len(rows) < 1:
        assert False, "There's no row for the created guild in the database"

    rows = DBManager.db_execute_select(
        f"""SELECT * FROM GuildWelcomeMessages WHERE guild_id = '{guild.id}';""")

    assert len(rows) != 0, "There's no row for the test created guild in the database"
    assert not len(rows) > 1, "There's duplicate rows for the test created guild in the database"
    message = rows[0]
    assert len(message) == 2, "Database row has incorrect number of columns. For some unknown reason."
    assert message[0] == guild.id and message[1] == 'default message'


@pytest.mark.asyncio
async def test_get_guild_welcome_message():
    DBManager.db_execute_commit(
        sql_str="""INSERT INTO GuildWelcomeMessages (guild_id,welcome_message) VALUES (1234567890, 'TestGetGuildWelcomeMessage');""")
    select = IntroCog.get_guild_welcome_message(1234567890)
    assert 'TestGetGuildWelcomeMessage' in select


@pytest.mark.asyncio
async def test_get_invalid_guild_welcome_message():
    """
    Test that invalid/nonexistent guilds get a default message
    """
    select = IntroCog.get_guild_welcome_message(404)
    assert 'default message' in select


@pytest.mark.asyncio
async def test_duplicate_guild_get_welcome_message():
    DBManager.db_execute_commit(
        sql_str="""INSERT INTO GuildWelcomeMessages (guild_id,welcome_message) VALUES (12345678908, 'FakeGuildTestMessage 1');""")
    DBManager.db_execute_commit(
        sql_str="""INSERT INTO GuildWelcomeMessages (guild_id,welcome_message) VALUES (12345678908, 'FakeGuildTestMessage 2');""")
    msg = IntroCog.get_guild_welcome_message(12345678908)
    assert 'FakeGuildTestMessage 1' in msg


@pytest.mark.asyncio
async def test_dm_group_message():
    welcome_message = IntroCog.get_guild_welcome_message(dpytest.get_config().guilds[0].id)
    test_member = dpytest.get_config().members[0]
    await (IntroCog.dm_group_message([test_member], welcome_message))
    dpytest.verify_message('default message', equals=False)


@pytest.mark.asyncio
async def test_on_member_join():
    test_config = dpytest.get_config()
    client = test_config.client
    guild = dpytest.back.make_guild('TestMemberJoin', id_num=1234)
    test_config.guilds.append(guild)
    await dpytest.member_join(1, client.user)
    await asyncio.sleep(0.5)
    welcome_message = IntroCog.get_guild_welcome_message(guild.id)
    await dpytest.member_join()
    dpytest.verify_message(welcome_message)


@pytest.mark.asyncio
async def test_on_member_join_after_update():
    test_welcome = "This is not a default message"
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + test_welcome)
    dpytest.verify_message('Y/N', equals=False)
    await asyncio.sleep(0.6)
    await dpytest.message('Y')
    await dpytest.member_join()
    dpytest.verify_message(IntroCog.get_guild_welcome_message(dpytest.get_config().guilds[0].id), equals=False)


@pytest.mark.asyncio
async def test_send_welcome_message():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "send_welcome_message")
    dpytest.verify_message('Are you sure you wish to do this? Y/N', equals=False)
    await dpytest.message('Y')
    dpytest.verify_message('default message', equals=False)


@pytest.mark.asyncio
async def test_cancel_send_welcome_message():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "send_welcome_message")
    await dpytest.message('N')
    dpytest.verify_message(f"Okay, I won't send the welcome message out.", equals=False)


@pytest.mark.asyncio
async def test_invalid_confirmation_send_welcome_message():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "send_welcome_message ")
    dpytest.verify_message('Y/N', False)
    await dpytest.message('3')
    dpytest.verify_message('Invalid input', False)


@pytest.mark.asyncio
async def test_lower_case_yes_confirmation_send_welcome_message():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "send_welcome_message ")
    dpytest.verify_message('Y/N', False)
    await dpytest.message('y')
    dpytest.verify_message('default message', False)


@pytest.mark.asyncio
async def test_lower_case_no_confirmation_send_welcome_message():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "send_welcome_message ")
    dpytest.verify_message('Y/N', False)
    await dpytest.message('n')
    dpytest.verify_message(f"Okay, I won't send the welcome message out.", equals=False)


@pytest.mark.asyncio
async def test_timeout_send_welcome_message():
    async def timeout_thread():
        with pytest.raises(asyncio.TimeoutError) as exc:
            await dpytest.message(KoalaBot.COMMAND_PREFIX + "send_welcome_message")
            dpytest.verify_message('Are you sure you wish to do this? Y/N')
            # Timer to force timeout

            async def stub():
                return

            t = threading.Timer(5.01, stub)
            t.start()
            t.join()
        assert exc.value == 'Timed out'
    timer = threading.Timer(5, timeout_thread)
    timer.start()
    timer.join()


@pytest.mark.asyncio
async def test_update_to_null_welcome_message():
    """
    Test that update_welcome_message doesn't fire without a parameter
    """
    old_message = IntroCog.get_guild_welcome_message(dpytest.get_config().guilds[0].id)
    with pytest.raises(discorderrors.MissingRequiredArgument):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message")
    dpytest.verify_message('Please put in a welcome message to update to.')
    assert old_message == IntroCog.get_guild_welcome_message(dpytest.get_config().guilds[0].id)


@pytest.mark.asyncio
async def test_update_welcome_message():
    guild = dpytest.get_config().guilds[0]
    test_welcome = "This should be updated in the database"
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + test_welcome)
    dpytest.verify_message('Y/N', equals=False)
    await dpytest.message('Y')
    dpytest.verify_message(equals=False, text='Not changing welcome')
    await asyncio.sleep(0.3)
    # Now verify the database hasn't been changed
    rows = DBManager.db_execute_select(f"""SELECT * FROM GuildWelcomeMessages WHERE guild_id = '{guild.id}';""")
    if len(rows) != 1:
        assert False, f"There are {len(rows)} rows for guild id {guild.id} in the database when there should only be 1"
    else:
        row = rows[0]
        if len(row) != 2:
            assert False, f"There's {len(row)} columns in this row. Check your table creation/setup code"
        else:
            assert row[1] == test_welcome


@pytest.mark.asyncio
async def test_cancel_update_welcome_message():
    guild = dpytest.get_config().guilds[0]
    test_welcome = "This should not be updated in the database"
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + test_welcome)
    dpytest.verify_message('Y/N', equals=False)
    await dpytest.message('N')
    dpytest.verify_message(equals=False, text='Not changing welcome')
    # Now verify the database hasn't been changed
    rows = DBManager.db_execute_select(f"""SELECT * FROM GuildWelcomeMessages WHERE guild_id = '{guild.id}';""")
    if len(rows) != 1:
        assert False, f"There are {len(rows)} rows for guild id {guild.id} in the database when there should only be 1"
    else:
        row = rows[0]
        if len(row) != 2:
            assert False, f"There's {len(row)} columns in this row. Check your table creation/setup code"
        else:
            assert row[1] != test_welcome


@pytest.mark.asyncio
async def test_invalid_confirmation_update_welcome_message():
    test_welcome = "This should not be updated in the database"
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + test_welcome)
    dpytest.verify_message('Y/N', False)
    await dpytest.message('3')
    dpytest.verify_message('Invalid input', False)


@pytest.mark.asyncio
async def test_timeout_update_welcome_message():
    async def timeout_thread():
        with pytest.raises(asyncio.TimeoutError) as exc:
            test_welcome = "This should not be updated in the database"
            await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + test_welcome)

            # Timer to force timeout
            async def stub():
                return

            t = threading.Timer(5.01, stub)
            t.start()
            t.join()
        assert exc.value == 'Timed out'
        assert test_welcome not in IntroCog.get_guild_welcome_message(dpytest.get_config().guilds[0].id)

    timer = threading.Timer(5, timeout_thread)
    timer.start()
    timer.join()


@pytest.fixture(scope='session', autouse=True)
def setup_db():
    DBManager.clear_all_tables(DBManager.fetch_all_tables())
    yield DBManager


@pytest.fixture(scope='function', autouse=True)
async def setup_clean_messages():
    await dpytest.empty_queue()
    yield dpytest
