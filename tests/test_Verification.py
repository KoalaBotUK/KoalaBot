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
TEST_EMAIL = 'verify_test@koalabot.uk'
TEST_EMAIL_DOMAIN = 'koalabot.uk'

# Variables
cog = None
db_manager = KoalaDBManager("verifyTest.db", KoalaBot.DB_KEY, KoalaBot.config_dir)
db_manager.create_base_tables()


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    cog = Verification.Verification(bot, db_manager)
    bot.add_cog(cog)
    dpytest.configure(bot)
    db_manager.db_execute_commit("DROP TABLE verified_emails")
    db_manager.db_execute_commit("DROP TABLE non_verified_emails")
    db_manager.db_execute_commit("DROP TABLE to_re_verify")
    db_manager.db_execute_commit("DROP TABLE roles")
    db_manager.db_execute_commit("CREATE TABLE verified_emails (u_id, email)")
    db_manager.db_execute_commit("CREATE TABLE non_verified_emails (u_id, email, token)")
    db_manager.db_execute_commit("CREATE TABLE to_re_verify (u_id, r_id)")
    db_manager.db_execute_commit("CREATE TABLE roles (s_id, r_id, email_suffix)")
    db_manager.insert_extension("Verify", 0, True, True)
    print("Tests starting")

@pytest.fixture(autouse=True)
def cog(bot):
    cog = Verification.Verification(bot, db_manager)
    bot.add_cog(cog)
    dpytest.configure(bot)
    db_manager.db_execute_commit("DROP TABLE verified_emails")
    db_manager.db_execute_commit("DROP TABLE non_verified_emails")
    db_manager.db_execute_commit("DROP TABLE to_re_verify")
    db_manager.db_execute_commit("DROP TABLE roles")
    db_manager.db_execute_commit("CREATE TABLE verified_emails (u_id, email)")
    db_manager.db_execute_commit("CREATE TABLE non_verified_emails (u_id, email, token)")
    db_manager.db_execute_commit("CREATE TABLE to_re_verify (u_id, r_id)")
    db_manager.db_execute_commit("CREATE TABLE roles (s_id, r_id, email_suffix)")
    db_manager.insert_extension("Verify", 0, True, True)
    print("Tests starting")
    return cog

@pytest.mark.asyncio
async def test_member_join_no_verify():
    await dpytest.member_join()
    assert dpytest.verify().message().nothing()


@pytest.mark.asyncio
async def test_member_join_verif_enabled():
    test_config = dpytest.get_config()
    guild = dpytest.back.make_guild("testMemberJoin", id_num=1234)
    test_config.guilds.append(guild)
    dpytest.back.make_role("testRole", guild, id_num=555)
    db_manager.db_execute_commit(f"INSERT INTO roles VALUES (1234, 555, '{TEST_EMAIL_DOMAIN}')")
    welcome_message = f"""Welcome to testMemberJoin. This guild has verification enabled.
Please verify one of the following emails to get the appropriate role using `{KoalaBot.COMMAND_PREFIX}verify your_email@example.com`.
This email is stored so you don't need to verify it multiple times across servers.
`{TEST_EMAIL_DOMAIN}` for `@testRole`"""
    await dpytest.member_join(1)
    await asyncio.sleep(0.25)
    assert dpytest.verify().message().content(welcome_message)
    db_manager.db_execute_commit("DELETE FROM roles WHERE s_id=1234")


@pytest.mark.asyncio
async def test_member_join_already_verified(bot):
    test_config = dpytest.get_config()
    guild = dpytest.back.make_guild("testMemberJoin", id_num=1234)
    bot.guilds.append(guild)

    test_user = dpytest.back.make_user("TestUser", 1234, id_num=999)
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    db_manager.db_execute_commit(f"INSERT INTO verified_emails VALUES (999, 'egg@{TEST_EMAIL_DOMAIN}')")
    db_manager.db_execute_commit(f"INSERT INTO roles VALUES (1234, 555, '{TEST_EMAIL_DOMAIN}')")
    await dpytest.member_join(guild, test_user)
    await asyncio.sleep(0.25)
    welcome_message = f"""Welcome to testMemberJoin. This guild has verification enabled.
Please verify one of the following emails to get the appropriate role using `{KoalaBot.COMMAND_PREFIX}verify your_email@example.com`.
This email is stored so you don't need to verify it multiple times across servers.
`{TEST_EMAIL_DOMAIN}` for `@testRole`"""
    assert dpytest.verify().message().content(welcome_message)
    member = guild.get_member(test_user.id)
    assert role in member.roles
    db_manager.db_execute_commit("DELETE FROM verified_emails WHERE u_id=999")
    db_manager.db_execute_commit("DELETE FROM roles WHERE s_id=1234")


@pytest.mark.asyncio
async def test_enable_verification():
    config = dpytest.get_config()
    guild = config.guilds[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + f"addVerification {TEST_EMAIL_DOMAIN} <@&555>")
    assert dpytest.verify().message().content(f"Verification enabled for <@&555> for emails ending with `{TEST_EMAIL_DOMAIN}`")
    entry = db_manager.db_execute_select("SELECT * FROM roles WHERE s_id=? AND r_id=?",
                                         (guild.id, role.id))
    assert entry
    db_manager.db_execute_commit(f"DELETE FROM roles WHERE s_id={guild.id}")


@pytest.mark.asyncio
async def test_disable_verification():
    config = dpytest.get_config()
    guild = config.guilds[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    db_manager.db_execute_commit(f"INSERT INTO roles VALUES ({guild.id}, 555, 'egg.com')")
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "removeVerification egg.com <@&555>")
    assert dpytest.verify().message().content("Emails ending with egg.com no longer give <@&555>")
    entry = db_manager.db_execute_select("SELECT * FROM roles WHERE s_id=? AND r_id=?",
                                         (guild.id, role.id))
    assert not entry


@pytest.mark.asyncio
async def test_verify():
    test_config = dpytest.get_config()
    guild = test_config.guilds[0]
    member = guild.members[0]
    dm = await member.create_dm()
    await dpytest.message(KoalaBot.COMMAND_PREFIX + f"verify {TEST_EMAIL}", dm)
    assert dpytest.verify().message().content("Please verify yourself using the command you have been emailed")
    entry = db_manager.db_execute_select(f"SELECT * FROM non_verified_emails WHERE u_id={member.id} AND email='{TEST_EMAIL}'")
    assert entry


@pytest.mark.asyncio
async def test_confirm():
    test_config = dpytest.get_config()
    guild = test_config.guilds[0]
    member = guild.members[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    db_manager.db_execute_commit(f"INSERT INTO roles VALUES ({guild.id}, 555, 'egg.com')")
    db_manager.db_execute_commit(f"INSERT INTO non_verified_emails VALUES ({member.id}, 'test@egg.com', 'testtoken')")
    dm = await member.create_dm()
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "confirm testtoken", dm)
    verified = db_manager.db_execute_select(f"SELECT * FROM verified_emails WHERE u_id={member.id} AND email='test@egg.com'")
    exists = db_manager.db_execute_select(f"SELECT * FROM non_verified_emails WHERE u_id={member.id} and email='test@egg.com'")
    assert verified
    assert not exists
    await asyncio.sleep(0.5)
    assert role in member.roles
    assert dpytest.verify().message().content("Your email has been verified, thank you")
    db_manager.db_execute_commit(f"DELETE FROM roles WHERE s_id={guild.id}")
    db_manager.db_execute_commit(f"DELETE FROM verified_emails WHERE u_id={member.id}")


@pytest.mark.asyncio
async def test_un_verify():
    test_config = dpytest.get_config()
    guild = test_config.guilds[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    member = test_config.members[0]
    await dpytest.add_role(member, role)
    db_manager.db_execute_commit(f"INSERT INTO verified_emails VALUES ({member.id}, 'test@egg.com')")
    db_manager.db_execute_commit(f"INSERT INTO roles VALUES ({guild.id}, {role.id}, 'egg.com')")
    dm = await member.create_dm()
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "unVerify test@egg.com", dm)
    assert dpytest.verify().message().content("test@egg.com has been un-verified and relevant roles have been removed")
    entry = db_manager.db_execute_select(f"SELECT * FROM verified_emails WHERE u_id={member.id} AND email='test@egg.com'")
    assert not entry
    assert role not in member.roles
    db_manager.db_execute_commit(f"DELETE FROM roles WHERE s_id={guild.id}")


@pytest.mark.asyncio
async def test_get_emails():
    db_manager.db_execute_commit(f"INSERT INTO verified_emails VALUES (123, '{TEST_EMAIL}')")
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "getEmails 123")
    assert dpytest.verify().message().content(f"""This user has registered with:\n{TEST_EMAIL}""")
    db_manager.db_execute_commit("DELETE FROM verified_emails WHERE u_id=123")


@pytest.mark.asyncio
async def test_re_verify():
    test_config = dpytest.get_config()
    guild = test_config.guilds[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    member = test_config.members[0]
    await dpytest.add_role(member, role)
    db_manager.db_execute_commit(f"INSERT INTO verified_emails VALUES ({member.id}, 'test@egg.com')")
    db_manager.db_execute_commit(f"INSERT INTO roles VALUES ({guild.id}, {role.id}, 'egg.com')")
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "reVerify <@&555>")
    assert role not in member.roles
    blacklisted = db_manager.db_execute_select(f"SELECT * FROM to_re_verify WHERE u_id={member.id}")
    assert blacklisted
    assert dpytest.verify().message().content("That role has now been removed from all users and they will need to re-verify the associated email.")
    db_manager.db_execute_commit(f"DELETE FROM verified_emails WHERE u_id={member.id}")
    db_manager.db_execute_commit(f"DELETE FROM roles WHERE s_id={guild.id}")
    db_manager.db_execute_commit(f"DELETE FROM to_re_verify WHERE u_id={member.id}")


@pytest.fixture(scope='session', autouse=True)
def setup_is_dpytest():
    KoalaBot.is_dpytest = True
    yield
    KoalaBot.is_dpytest = False