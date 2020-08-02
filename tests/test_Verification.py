#!/usr/bin/env python
# TODO Test rig broken, restart from beginning and fix.
"""
Testing KoalaBot IntroCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import asyncio
# Libs
import discord.ext.test as dpytest
import pytest
from discord.ext import commands

# Own modules
import KoalaBot
from cogs import Verification
from utils.KoalaDBManager import KoalaDBManager

# Constants

# Variables
cog = None
DBManager = KoalaDBManager("../" + KoalaBot.DATABASE_PATH)
DBManager.create_base_tables()


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    cog = Verification.Verification(bot)
    bot.add_cog(cog)
    dpytest.configure(bot)
    DBManager.db_execute_commit("CREATE TABLE IF NOT EXISTS server_info (guild_id, role_id, domain)")
    DBManager.db_execute_commit(
            "CREATE TABLE IF NOT EXISTS verified_users (guild_id, user_id, domain, token, verified, role_assigned)")
    print("Tests starting")


@pytest.mark.asyncio
async def test_member_join_no_verify():
    await dpytest.member_join()
    dpytest.verify_message(assert_nothing=True)


@pytest.mark.asyncio
async def test_member_join_with_verify():
    g_id = dpytest.get_config().guilds[0].id
    DBManager.db_execute_commit(f"INSERT INTO server_info values ({g_id}, 1, 'test.com')")
    await dpytest.member_join()
    await asyncio.sleep(1)
    dpytest.verify_message(f"Hi, I see you've logged in. Please verify with an allowed email address with `k!verify {g_id} <email>`")
    DBManager.db_execute_commit(f"DELETE FROM server_info WHERE guild_id={g_id}")


@pytest.mark.asyncio
async def test_enable_no_role():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "enable_verification domain.com")
    await asyncio.sleep(1)
    dpytest.verify_message(
        f"Please provide the correct arguments (`{KoalaBot.COMMAND_PREFIX}enable_verification <domain> <@role>`")


@pytest.mark.asyncio
async def test_enable_no_domain():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "enable_verification <@&735446401919615037>")
    await asyncio.sleep(1)
    dpytest.verify_message(
        f"Please provide the correct arguments (`{KoalaBot.COMMAND_PREFIX}enable_verification <domain> <@role>`")


@pytest.mark.asyncio
async def test_enable_invalid_role_1():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "enable_verification domain.com test")
    await asyncio.sleep(1)
    dpytest.verify_message("Please give a role by @mentioning it")


@pytest.mark.asyncio
async def test_enable_invalid_role_2():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "enable_verification domain.com <@&100>")
    await asyncio.sleep(1)
    dpytest.verify_message("Please supply a valid role")


@pytest.mark.asyncio
async def test_enable_invalid_domain():
    test_config = dpytest.get_config()
    dpytest.back.make_role("test", test_config.guilds[0], id_num=735446401919615037)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "enable_verification spaghetti <@&735446401919615037>")
    await asyncio.sleep(1)
    dpytest.verify_message("Please provide a valid domain")


@pytest.mark.asyncio
async def test_enable_already_enabled():
    test_config = dpytest.get_config()
    dpytest.back.make_role("test", test_config.guilds[0], id_num=735446401919615037)
    guild_id = test_config.guilds[0].id
    DBManager.db_execute_commit(f"INSERT INTO server_info values ({guild_id}, 735446401919615037, 'soton.ac.uk')")
    await asyncio.sleep(1)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "enable_verification soton.ac.uk <@&735446401919615037>")
    await asyncio.sleep(1)
    DBManager.db_execute_commit(f"DELETE FROM server_info WHERE guild_id={guild_id}")
    dpytest.verify_message("Verification is already enabled for that role")


@pytest.mark.asyncio
async def test_enable_valid_input():
    test_config = dpytest.get_config()
    dpytest.back.make_role("test", test_config.guilds[0], id_num=735446401919615037)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "enable_verification soton.ac.uk <@&735446401919615037>")
    await asyncio.sleep(1)
    dpytest.verify_message("Verification enabled for <@&735446401919615037> for emails with the domain soton.ac.uk")
    entry = DBManager.db_execute_select(f"SELECT * FROM server_info WHERE guild_id={dpytest.get_config().guilds[0].id} AND role_id=735446401919615037 AND domain=?", args=("soton.ac.uk",))
    assert entry
    DBManager.db_execute_commit(f"DELETE FROM server_info WHERE guild_id={dpytest.get_config().guilds[0].id}")


@pytest.mark.asyncio
async def test_disable_no_role():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "disable_verification domain.com")
    await asyncio.sleep(1)
    dpytest.verify_message(
        f"Please provide the correct arguments (`{KoalaBot.COMMAND_PREFIX}enable_verification <domain> <@role>`")


@pytest.mark.asyncio
async def test_disable_no_domain():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "disable_verification <@&735446401919615037>")
    await asyncio.sleep(1)
    dpytest.verify_message(
        f"Please provide the correct arguments (`{KoalaBot.COMMAND_PREFIX}enable_verification <domain> <@role>`")


@pytest.mark.asyncio
async def test_disable_invalid_role():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "disable_verification domain.com test")
    await asyncio.sleep(1)
    dpytest.verify_message("Please give a role by @mentioning it")


@pytest.mark.asyncio
async def test_disable_valid_args():
    test_config = dpytest.get_config()
    dpytest.back.make_role("test", test_config.guilds[0], id_num=735446401919615037)
    DBManager.db_execute_commit("INSERT INTO server_info VALUES (?, ?, ?)",
                                (test_config.guilds[0].id, 735446401919615037, "domain.com"))
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "disable_verification domain.com <@&735446401919615037>")
    dpytest.verify_message("Emails with domain.com no longer give <@&735446401919615037>")
    entry = DBManager.db_execute_select("SELECT * FROM server_info WHERE domain=? AND guild_id=? AND role_id=?",
                                        ("domain.com", test_config.guilds[0].id, 735446401919615037))
    assert not entry
    DBManager.db_execute_commit("DELETE FROM server_info WHERE domain=? AND guild_id=? AND role_id=?",
                                ("domain.com", test_config.guilds[0].id, 735446401919615037))


@pytest.mark.asyncio
async def test_verification_valid_args():
    test_config = dpytest.get_config()
    guild = test_config.guilds[0]
    member = guild.members[0]
    dpytest.back.make_role("test", guild, id_num=735446401919615037)
    DBManager.db_execute_commit("INSERT INTO server_info VALUES (?, ?, ?)",
                                (guild.id, 735446401919615037, "domain.com"))
    dm = await member.create_dm()
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}verify {test_config.guilds[0].id} test@domain.com", dm)
    entry = DBManager.db_execute_select("SELECT * FROM verified_users WHERE guild_id=? AND user_id=?",
                                        (guild.id, member.id))
    assert entry
    dpytest.verify_message("Please verify yourself by clicking the link in your email")
    DBManager.db_execute_commit("DELETE FROM server_info WHERE guild_id=? AND role_id=?",
                                (guild.id, 735446401919615037))
    DBManager.db_execute_commit("DELETE FROM verified_users WHERE guild_id=? AND user_id=?",
                                (guild.id, member.id))



