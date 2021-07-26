#!/usr/bin/env python
"""
Testing KoalaBot IntroCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

import asyncio

# Libs
import discord.ext.test as dpytest
import discord.ext.test.factories as dpyfactory
import mock
import pytest
from discord.ext import commands

# Own modules
import KoalaBot
from cogs import IntroCog
from tests.utils_testing.LastCtxCog import LastCtxCog
from utils.KoalaDBManager import KoalaDBManager

# Constants
fake_guild_id = 1000
non_existent_guild_id = 9999

# Variables
DBManager = KoalaDBManager(KoalaBot.DATABASE_PATH, KoalaBot.DB_KEY, KoalaBot.config_dir)
DBManager.create_base_tables()


@pytest.fixture(autouse=True)
def utils_cog(bot):
    utils_cog = LastCtxCog(bot)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    print("Tests starting")
    return utils_cog

@pytest.fixture(autouse=True)
def intro_cog(bot):
    intro_cog = IntroCog.IntroCog(bot)
    bot.add_cog(intro_cog)
    dpytest.configure(bot)
    print("Tests starting")
    return intro_cog


# Welcome Message Database Manager Tests

@pytest.mark.parametrize("guild_id, expected", [(101,
                                                 "fake guild welcome message"),
                                                (non_existent_guild_id, None)])
@pytest.mark.asyncio
async def test_db_manager_fetch_welcome_message(guild_id, expected):
    await add_fake_guild_to_db(101)
    val = DBManager.fetch_guild_welcome_message(guild_id)
    assert val == expected, str(guild_id) + f": {val}"


@pytest.mark.parametrize("guild_id, new_message, expected", [(111, "non-default message", "non-default message"), (
        222, "you're here! you're gonna have fun", "you\'re here! you\'re gonna have fun"), (333, '', ''),
                                                             (444, None, None)])
@pytest.mark.asyncio
async def test_db_manager_update_welcome_message(guild_id, new_message, expected):
    await add_fake_guild_to_db(guild_id)
    DBManager.update_guild_welcome_message(guild_id, new_message)
    await asyncio.sleep(0.2)
    val = DBManager.fetch_guild_welcome_message(guild_id)
    assert val == expected, DBManager.fetch_guild_welcome_message(guild_id)


@pytest.mark.asyncio
async def test_db_manager_new_guild_welcome_message():
    val = DBManager.new_guild_welcome_message(fake_guild_id)
    assert val == IntroCog.DEFAULT_WELCOME_MESSAGE


@pytest.mark.parametrize("guild_id, expected", [(fake_guild_id, 1), (non_existent_guild_id, 0)])
@pytest.mark.asyncio
async def test_db_manager_remove_guild_welcome_message(guild_id, expected):
    count = DBManager.remove_guild_welcome_message(guild_id)
    assert count == expected


# Welcome Message Discord-based tests

@pytest.mark.asyncio
async def test_on_guild_join():
    test_config = dpytest.get_config()
    client = test_config.client
    guild = dpytest.back.make_guild('TestGuildJoin', id_num=1250)
    test_config.guilds.append(guild)
    await dpytest.member_join(1, client.user)
    await asyncio.sleep(0.3)
    val = DBManager.fetch_guild_welcome_message(1250)
    assert val == IntroCog.DEFAULT_WELCOME_MESSAGE


@pytest.mark.asyncio
async def test_on_guild_remove(bot):
    test_config = dpytest.get_config()
    guild = test_config.guilds[0]
    client = test_config.client
    bot_member = test_config.guilds[0].get_member(client.user.id)
    dpytest.backend.delete_member(bot_member)
    val = DBManager.fetch_guild_welcome_message(guild.id)
    assert val is None


@pytest.mark.parametrize("guild_id, expected",
                         [(101, f"fake guild welcome message"), (1250, IntroCog.DEFAULT_WELCOME_MESSAGE),
                          (9999, IntroCog.DEFAULT_WELCOME_MESSAGE)])
@pytest.mark.asyncio
async def test_get_guild_welcome_message(guild_id, expected):
    val = IntroCog.get_guild_welcome_message(guild_id)
    assert val == f"{expected}\r\n{IntroCog.BASE_LEGAL_MESSAGE}", val


@pytest.mark.asyncio
async def test_get_non_bot_members():
    test_config = dpytest.get_config()
    client = test_config.client
    guild = test_config.guilds[0]
    assert len(IntroCog.get_non_bot_members(guild)) == 1, [non_bot_member.name for non_bot_member in
                                                           IntroCog.get_non_bot_members(guild)]
    await dpytest.member_join()
    assert len(IntroCog.get_non_bot_members(guild)) == 2, [non_bot_member.name for non_bot_member in
                                                           IntroCog.get_non_bot_members(guild)]
    for i in range(3):
        await dpytest.member_join(name=f'TestUser{str(i)}')
    assert len(IntroCog.get_non_bot_members(guild)) == 5, [non_bot_member.name for non_bot_member in
                                                           IntroCog.get_non_bot_members(guild)]
    print(
        [str(non_bot_member) + " " + str(non_bot_member.bot) for non_bot_member in IntroCog.get_non_bot_members(guild)])
    dpytest.backend.delete_member(guild.get_member(client.user.id))
    assert len(IntroCog.get_non_bot_members(guild)) == 5, [non_bot_member.name for non_bot_member in
                                                           IntroCog.get_non_bot_members(guild)]
    print(
        [str(non_bot_member) + " " + str(non_bot_member.bot) for non_bot_member in IntroCog.get_non_bot_members(guild)])


@pytest.mark.asyncio
async def test_on_member_join():
    test_config = dpytest.get_config()
    client = test_config.client
    guild = dpytest.back.make_guild('TestMemberJoin', id_num=1234)
    test_config.guilds.append(guild)
    await dpytest.member_join(1, client.user)
    await asyncio.sleep(0.25)
    welcome_message = IntroCog.get_guild_welcome_message(guild.id)
    await dpytest.member_join(1)
    assert dpytest.verify().message().content(welcome_message)
    DBManager.update_guild_welcome_message(guild.id, 'This is an updated welcome message.')
    await asyncio.sleep(0.25)
    welcome_message = IntroCog.get_guild_welcome_message(guild.id)
    await dpytest.member_join(1)
    assert dpytest.verify().message().content(welcome_message)


@pytest.mark.asyncio
async def test_wait_for_message(utils_cog):
    bot = dpytest.get_config().client
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx = utils_cog.get_last_ctx()

    import threading
    t2 = threading.Timer(interval=0.2, function=dpytest.message, args=("y"))
    t2.start()
    fut = IntroCog.wait_for_message(bot, ctx)
    t2.join()
    assert fut, dpytest.sent_queue


@pytest.mark.asyncio
async def test_wait_for_message_timeout(utils_cog):
    bot = dpytest.get_config().client
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx = utils_cog.get_last_ctx()
    with pytest.raises(asyncio.TimeoutError):
        await IntroCog.wait_for_message(bot, ctx, 0.2)


@pytest.mark.parametrize("msg_content, is_invalid, expected",
                         [('y', False, True), ('n', False, False), ('Y', False, True), ('N', False, False),
                          ('x', True, False), (' ', True, False), ('', True, False), ('yy', True, False)])
@pytest.mark.asyncio
async def test_ask_for_confirmation(msg_content, is_invalid, expected):
    author = dpytest.get_config().members[0]
    channel = dpytest.get_config().channels[0]
    message = dpytest.back.make_message(author=author, content=msg_content, channel=channel)
    x = await IntroCog.ask_for_confirmation(message, channel)
    assert x == expected
    if is_invalid:
        assert dpytest.verify().message()


@pytest.mark.parametrize("msg_content, expected",
                         [('y', True), ('n', False), ('Y', True), ('N', False), ('', None), (' ', None),
                          ('y ', True), (' n', False)])
@pytest.mark.asyncio
async def test_confirm_message(msg_content, expected):
    author = dpytest.get_config().members[0]
    channel = dpytest.get_config().channels[0]
    message = dpytest.back.make_message(author=author, content=msg_content, channel=channel)
    x = await IntroCog.confirm_message(message)
    assert x is expected


@pytest.mark.asyncio
async def test_send_welcome_message():
    msg_mock = dpytest.back.make_message('y', dpytest.get_config().members[0], dpytest.get_config().channels[0])
    with mock.patch('cogs.IntroCog.wait_for_message', mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "send_welcome_message")
    assert dpytest.verify().message().content("This will DM 1 people. Are you sure you wish to do this? Y/N")
    assert dpytest.verify().message().content("Okay, sending out the welcome message now.")
    assert dpytest.verify().message().content(f"{IntroCog.DEFAULT_WELCOME_MESSAGE}\r\n{IntroCog.BASE_LEGAL_MESSAGE}")


@pytest.mark.asyncio
async def test_send_welcome_message_cancelled():
    msg_mock = dpytest.back.make_message('n', dpytest.get_config().members[0], dpytest.get_config().channels[0])
    with mock.patch('cogs.IntroCog.wait_for_message', mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "send_welcome_message")
    assert dpytest.verify().message().content("This will DM 1 people. Are you sure you wish to do this? Y/N")
    assert dpytest.verify().message().content("Okay, I won't send out the welcome message then.")
    assert dpytest.verify().message().nothing()


@pytest.mark.asyncio
async def test_send_welcome_message_timeout():
    with mock.patch('cogs.IntroCog.wait_for_message', mock.AsyncMock(return_value=None)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "send_welcome_message")
        assert dpytest.verify().message().content("This will DM 1 people. Are you sure you wish to do this? Y/N")
        assert dpytest.verify().message().content('Timed out.')
        assert dpytest.verify().message().content("Okay, I won't send out the welcome message then.")
        assert dpytest.verify().message().nothing()


@pytest.mark.asyncio
async def test_cancel_update_welcome_message():
    guild = dpytest.get_config().guilds[0]
    old_message = IntroCog.get_guild_welcome_message(guild.id)
    new_message = "this is a non default message"
    msg_mock = dpytest.back.make_message('n', dpytest.get_config().members[0], dpytest.get_config().channels[0])
    with mock.patch('cogs.IntroCog.wait_for_message', mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + new_message)

    assert dpytest.verify().message().content(f"""Your current welcome message is:\n\r{old_message}""")
    assert dpytest.verify().message().content(f"""Your new welcome message will be:\n\r{new_message}\n\r{IntroCog.BASE_LEGAL_MESSAGE}""" +
                           """\n\rWould you like to update the message? Y/N?""")
    assert dpytest.verify().message().content("Okay, I won't update the welcome message then.")
    assert dpytest.verify().message().nothing()
    assert DBManager.fetch_guild_welcome_message(guild.id) != new_message


@pytest.mark.asyncio
async def test_update_welcome_message():
    guild = dpytest.get_config().guilds[0]
    old_message = IntroCog.get_guild_welcome_message(guild.id)
    new_message = "this is a non default message"
    msg_mock = dpytest.back.make_message('y', dpytest.get_config().members[0], dpytest.get_config().channels[0])
    with mock.patch('cogs.IntroCog.wait_for_message', mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + new_message)

    assert dpytest.verify().message().content(f"""Your current welcome message is:\n\r{old_message}""")
    assert dpytest.verify().message().content(f"""Your new welcome message will be:\n\r{new_message}\n\r{IntroCog.BASE_LEGAL_MESSAGE}""" +
                           """\n\rWould you like to update the message? Y/N?""")
    assert dpytest.verify().message().content("Okay, updating the welcome message of the guild in the database now.")
    assert dpytest.verify().message().content("Updated in the database, your new welcome message is this is a non default message.")
    assert dpytest.verify().message().nothing()
    assert DBManager.fetch_guild_welcome_message(guild.id) == new_message


@pytest.mark.asyncio
async def test_update_welcome_message_too_long():
    import random, string
    guild = dpytest.get_config().guilds[0]
    old_message = IntroCog.get_guild_welcome_message(guild.id)
    new_message = "".join(random.choice(string.ascii_letters) for _ in range(1800))
    msg_mock = dpytest.back.make_message('y', dpytest.get_config().members[0], dpytest.get_config().channels[0])
    with mock.patch('cogs.IntroCog.wait_for_message', mock.AsyncMock(return_value=msg_mock)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + new_message)
    assert dpytest.verify().message().content("Your welcome message is too long to send, sorry. The maximum character limit is 1600.")
    assert dpytest.verify().message().nothing()
    assert DBManager.fetch_guild_welcome_message(guild.id) != new_message


@pytest.mark.asyncio
async def test_update_welcome_message_no_args():
    with pytest.raises(commands.MissingRequiredArgument):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message")
    assert dpytest.verify().message().content("Please put in a welcome message to update to.")


@pytest.mark.asyncio
async def test_view_welcome_message():
    guild = dpytest.get_config().guilds[0]
    old_message = IntroCog.get_guild_welcome_message(guild.id)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "welcomeViewMsg ")
    assert dpytest.verify().message().content(f"""Your current welcome message is:\n\r{old_message}""")


@pytest.mark.asyncio
async def test_update_welcome_message_timeout():
    guild = dpytest.get_config().guilds[0]
    old_message = IntroCog.get_guild_welcome_message(guild.id)
    new_message = "this is a non default message"
    # msg_mock = dpytest.back.make_message('y', dpytest.get_config().members[0], dpytest.get_config().channels[0])
    with mock.patch('cogs.IntroCog.wait_for_message', mock.AsyncMock(return_value=None)):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "update_welcome_message " + new_message)

    assert dpytest.verify().message().content(f"""Your current welcome message is:\n\r{old_message}""")
    assert dpytest.verify().message().content(f"""Your new welcome message will be:\n\r{new_message}\n\r{IntroCog.BASE_LEGAL_MESSAGE}""" +
                           """\n\rWould you like to update the message? Y/N?""")
    assert dpytest.verify().message().content("Timed out.")
    assert dpytest.verify().message().content("Okay, I won't update the welcome message then.")
    assert dpytest.verify().message().nothing()
    assert DBManager.fetch_guild_welcome_message(guild.id) != new_message


@pytest.fixture(scope='session', autouse=True)
def setup_db():
    DBManager.clear_all_tables(DBManager.fetch_all_tables())
    yield DBManager





@pytest.fixture(scope='function', autouse=True)
async def setup_clean_messages():
    await dpytest.empty_queue()
    yield dpytest


async def add_fake_guild_to_db(id=-1):
    if id == 9999:
        return -1
    if id == -1:
        id = dpyfactory.make_id()
    DBManager.remove_guild_welcome_message(id)
    DBManager.db_execute_commit(
        f"INSERT INTO GuildWelcomeMessages (guild_id, welcome_message) VALUES ({id}, 'fake guild welcome message');")
    return id
