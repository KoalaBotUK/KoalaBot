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
import discord.ext.commands.errors as discorderrors
import discord.ext.test as dpytest
import pytest
from discord.ext import commands
import mock
import threading
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
    guild = dpytest.get_config().guilds[0]
    # Try testing guild join on startup
    rows = DBManager.db_execute_select(
        f"""SELECT * FROM GuildWelcomeMessages WHERE guild_id = '{guild.id}';""")

    if len(rows) < 1:
        assert False, "There's no row for the created guild in the database"

    with pytest.raises(RuntimeError) as exc:
        rows = DBManager.db_execute_select(
            f"""SELECT * FROM GuildWelcomeMessages WHERE guild_id = '{guild.id}';""")
        assert len(rows) != 0, "There's no row for the test created guild in the database"
        assert len(rows) > 1, "There's duplicate rows for the test created guild in the database"
        message = rows[0]
        assert len(message) == 2, "Database row has incorrect number of columns. For some unknown reason."
        assert message[0] == guild.id and message[1] == 'default message'
    assert exc is None

    """test_config = dpytest.get_config()
    client = test_config.client
    guild = dpytest.back.make_guild('TestGuildJoin')
    test_config.guilds.append(guild)
    await dpytest.member_join(1, client.user)
    rows = DBManager.db_execute_select(
        f\"""SELECT * FROM GuildWelcomeMessages WHERE guild_id = '{guild.id}';\""")

    if len(rows) == 1:
        row = rows[0]
        assert row[1] == 'default message', "Wrong message in row."
    else:
        for r in rows:
            print(str(r[1]) + "\r\n")
        # If there's zero/more than one entry right now, there's an issue. Raise an error
        assert False, f"{len(rows)} entries for this guild (id = {guild.id}) found in the database. Check guild_join listener"
    """


@pytest.mark.asyncio
async def test_get_guild_welcome_message():
    DBManager.db_execute_commit(sql_str="""INSERT INTO GuildWelcomeMessages (guild_id,welcome_message) VALUES (1234567890, 'TestGetGuildWelcomeMessage');""")
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
    with pytest.raises(RuntimeError):
        msg = IntroCog.get_guild_welcome_message(12345678908)
    assert False, msg


@pytest.mark.asyncio
async def test_dm_welcome_message():
    welcome_message = IntroCog.get_guild_welcome_message(dpytest.get_config().guilds[0].id)
    test_member = dpytest.get_config().members[0]
    await (IntroCog.dm_welcome_message([test_member], welcome_message))
    dpytest.verify_message('default message', equals=False)


@pytest.mark.asyncio
async def test_on_member_join():
    welcome_message = IntroCog.get_guild_welcome_message(dpytest.get_config().guilds[0].id)
    member = await dpytest.member_join()

    msg = dpytest.verify_message()
    assert welcome_message in msg.content
    dpytest.verify_message(welcome_message, equals=False)


@pytest.mark.asyncio
async def test_send_welcome_message():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "send_welcome_message")
    await dpytest.message('Y')
    dpytest.verify_message('default message', equals=False)


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
async def test_invalid_yes_no_input():
    test_welcome = "This should not be updated in the database"
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + test_welcome)
    dpytest.verify_message('Y/N', False)
    await dpytest.message('3')
    dpytest.verify_message('Invalid input', False)


@pytest.mark.asyncio
async def test_update_to_null_welcome_message():
    """
    Test that update_welcome_message doesn't fire without a parameter
    """
    with pytest.raises(discorderrors.MissingRequiredArgument) as exc:
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message")
    assert str(exc.value) == 'new_message is a required argument that is missing.'


@pytest.mark.asyncio
async def test_update_welcome_message():
    guild = dpytest.get_config().guilds[0]
    test_welcome = "This is not a default message"
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + test_welcome)
    dpytest.verify_message('Y/N', equals=False)
    await dpytest.message('Y')
    dpytest.verify_message(equals=False, text='new custom part of the message')
    # Now verify the database hasn't been changed
    rows = DBManager.db_execute_select(f"""SELECT * FROM GuildWelcomeMessages WHERE guild_id = '{guild.id}';""")

    if len(rows) != 1:
        assert False, f"There are {len(rows)} rows for guild id {guild.id} in the database when there should only be 1"
    else:
        row = rows[0]
        if len(row) != 2:
            assert False, f"There's {len(row)} columns in this row. Check your table creation/setup code"
        else:
            # dpytest.verify_message(test_welcome, False)
            assert row[1] == test_welcome, row[1]


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
async def test_timeout_update_welcome_message():
    async def timeout_thread():
        with pytest.raises(asyncio.TimeoutError) as exc:
            test_welcome = "This should not be updated in the database"
            await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + test_welcome)

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


@pytest.fixture(scope='function', autouse=True)
def setup_db():
    yield DBManager
    # DBManager.clear_all_tables(DBManager.fetch_all_tables())
