#!/usr/bin/env python

"""
Testing KoalaBot ReactForRole Cog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import random
from typing import *

# Libs
import discord
import discord.ext.test as dpytest
import emoji
import mock
import pytest
from discord.ext.test import factories as dpyfactory

# Own modules
from koala.db import session_manager
from tests.tests_utils import utils as testutils

from tests.log import logger
from koala.cogs.react_for_role.db import *
from .utils import independent_get_guild_rfr_message, independent_get_rfr_message_emoji_role, \
    independent_get_guild_rfr_required_role, get_rfr_reaction_role_by_role_id


# Constants

# Variables


@pytest.mark.asyncio
async def test_rfr_db_functions_guild_rfr_messages():
    with session_manager() as session:
        guild: discord.Guild = dpytest.get_config().guilds[0]
        channel: discord.TextChannel = dpytest.get_config().channels[0]
        msg_id = dpyfactory.make_id()
        # Test when no messages exist
        expected_full_list: List[Tuple[int, int, int, int]] = []
        assert independent_get_guild_rfr_message(
            session, guild.id, channel.id, msg_id) == expected_full_list
        assert independent_get_guild_rfr_message(session) == expected_full_list
        # Test on adding first message, 1 message, 1 channel, 1 guild
        add_rfr_message(guild.id, channel.id, msg_id)
        expected_full_list.append((guild.id, channel.id, msg_id, 1))
        assert independent_get_guild_rfr_message(session) == expected_full_list
        assert independent_get_guild_rfr_message(session, guild.id, channel.id, msg_id) == [
            expected_full_list[0]]
        # 2 guilds, 1 channel each, 2 messages
        guild2: discord.Guild = dpytest.back.make_guild("TestGuild2")
        channel2: discord.TextChannel = dpytest.back.make_text_channel(
            "TestGuild2Channel1", guild2)
        msg_id = dpyfactory.make_id()
        dpytest.get_config().guilds.append(guild2)
        add_rfr_message(guild2.id, channel2.id, msg_id)
        expected_full_list.append((guild2.id, channel2.id, msg_id, 2))
        assert independent_get_guild_rfr_message(session, guild2.id, channel2.id, msg_id) == [
            expected_full_list[1]]
        assert independent_get_guild_rfr_message(session, guild2.id, channel2.id, msg_id)[
                   0] == get_rfr_message(guild2.id,
                                                   channel2.id,
                                                   msg_id)
        assert independent_get_guild_rfr_message(session) == expected_full_list
        # 1 guild, 2 channels with 1 message each
        guild1channel2: discord.TextChannel = dpytest.back.make_text_channel(
            "TestGuild1Channel2", guild)
        msg_id = dpyfactory.make_id()
        add_rfr_message(guild.id, guild1channel2.id, msg_id)
        expected_full_list.append((guild.id, guild1channel2.id, msg_id, 3))
        assert independent_get_guild_rfr_message(
            session, guild.id, guild1channel2.id, msg_id) == [expected_full_list[2]]
        assert independent_get_guild_rfr_message(session, guild.id, guild1channel2.id, msg_id)[
                   0] == get_rfr_message(
            guild.id, guild1channel2.id, msg_id)
        assert independent_get_guild_rfr_message(session) == expected_full_list
        assert independent_get_guild_rfr_message(session,
                                                 guild.id) == [expected_full_list[0], expected_full_list[2]]
        # 1 guild, 1 channel, with 2 messages
        msg_id = dpyfactory.make_id()
        add_rfr_message(guild.id, channel.id, msg_id)
        expected_full_list.append((guild.id, channel.id, msg_id, 4))
        assert independent_get_guild_rfr_message(session, guild.id, channel.id, msg_id) == [
            expected_full_list[3]]
        assert independent_get_guild_rfr_message(session, guild.id, channel.id, msg_id)[0] == get_rfr_message(
            guild.id,
            channel.id,
            msg_id)
        assert independent_get_guild_rfr_message(session) == expected_full_list
        assert independent_get_guild_rfr_message(session, guild.id, channel.id) == [
            expected_full_list[0], expected_full_list[3]]
        # remove all messages
        guild_rfr_messages = independent_get_guild_rfr_message(session)
        for guild_rfr_message in guild_rfr_messages:
            assert guild_rfr_message in guild_rfr_messages
            remove_rfr_message(
                guild_rfr_message[0], guild_rfr_message[1], guild_rfr_message[2])
            assert guild_rfr_message not in independent_get_guild_rfr_message(session)
        assert independent_get_guild_rfr_message(session) == []


@pytest.mark.asyncio
async def test_rfr_db_functions_rfr_message_emoji_roles():
    with session_manager() as session:
        guild: discord.Guild = dpytest.get_config().guilds[0]
        channel: discord.TextChannel = dpytest.get_config().channels[0]
        msg_id = dpyfactory.make_id()
        add_rfr_message(guild.id, channel.id, msg_id)
        guild_rfr_message = independent_get_guild_rfr_message(session)[0]
        expected_full_list: List[Tuple[int, str, int]] = []
        assert independent_get_rfr_message_emoji_role(session) == expected_full_list
        # 1 unicode, 1 role
        fake_emoji_1 = testutils.fake_unicode_emoji()
        fake_role_id_1 = dpyfactory.make_id()
        expected_full_list.append((1, fake_emoji_1, fake_role_id_1))
        add_rfr_message_emoji_role(
            guild_rfr_message[3], fake_emoji_1, fake_role_id_1)
        assert independent_get_rfr_message_emoji_role(
            session) == expected_full_list, get_rfr_message_emoji_roles(1)
        assert independent_get_rfr_message_emoji_role(session, 1) == expected_full_list
        assert independent_get_rfr_message_emoji_role(session, guild_rfr_message[3], fake_emoji_1,
                                                      fake_role_id_1) == [get_rfr_reaction_role(
            guild_rfr_message[3], fake_emoji_1, fake_role_id_1)]
        # 1 unicode, 1 custom, trying to get same role
        fake_emoji_2 = testutils.fake_custom_emoji_str_rep()
        add_rfr_message_emoji_role(
            guild_rfr_message[3], fake_emoji_2, fake_role_id_1)
        assert independent_get_rfr_message_emoji_role(session) == expected_full_list
        assert independent_get_rfr_message_emoji_role(session,
                                                      guild_rfr_message[3]) == get_rfr_message_emoji_roles(
            guild_rfr_message[3])
        assert [get_rfr_reaction_role(
            guild_rfr_message[3], fake_emoji_2, fake_role_id_1)] == [None]
        # 2 roles, with 1 emoji trying to give both roles
        fake_role_id_2 = dpyfactory.make_id()
        add_rfr_message_emoji_role(
            guild_rfr_message[3], fake_emoji_1, fake_role_id_2)
        assert independent_get_rfr_message_emoji_role(session) == expected_full_list
        assert independent_get_rfr_message_emoji_role(session,
                                                      guild_rfr_message[3]) == get_rfr_message_emoji_roles(
            guild_rfr_message[3])
        assert [get_rfr_reaction_role(
            guild_rfr_message[3], fake_emoji_1, fake_role_id_2)] == [None]

        # 2 roles, 2 emojis, 1 message. split between them
        fake_emoji_2 = testutils.fake_custom_emoji_str_rep()
        fake_role_id_2 = dpyfactory.make_id()
        expected_full_list.append((1, fake_emoji_2, fake_role_id_2))
        add_rfr_message_emoji_role(*expected_full_list[1])
        assert independent_get_rfr_message_emoji_role(session) == expected_full_list
        assert independent_get_rfr_message_emoji_role(session,
                                                      1, fake_emoji_1) == [(1, fake_emoji_1, fake_role_id_1)]
        assert independent_get_rfr_message_emoji_role(session,
                                                      1, fake_emoji_2) == [(1, fake_emoji_2, fake_role_id_2)]
        assert independent_get_rfr_message_emoji_role(session, 1, fake_emoji_1)[0][
                   2] == get_rfr_reaction_role_by_emoji_str(1,
                                                                      fake_emoji_1)
        assert independent_get_rfr_message_emoji_role(session,
                                                      1) == get_rfr_message_emoji_roles(1)
        assert independent_get_rfr_message_emoji_role(session, 1, role_id=fake_role_id_2)[0][
                   2] == get_rfr_reaction_role_by_role_id(session, emoji_role_id=1, role_id=fake_role_id_2)

        # 2 roles 2 emojis, 2 messages. duplicated messages
        msg2_id = dpyfactory.make_id()
        add_rfr_message(guild.id, channel.id, msg2_id)
        assert independent_get_guild_rfr_message(session
                                                 ) == [guild_rfr_message, (guild.id, channel.id, msg2_id, 2)]
        guild_rfr_message_2 = independent_get_guild_rfr_message(session)[1]
        add_rfr_message_emoji_role(
            guild_rfr_message_2[3], fake_emoji_1, fake_role_id_1)
        add_rfr_message_emoji_role(
            guild_rfr_message_2[3], fake_emoji_2, fake_role_id_2)
        expected_full_list.extend([(guild_rfr_message_2[3], fake_emoji_1, fake_role_id_1),
                                   (guild_rfr_message_2[3], fake_emoji_2, fake_role_id_2)])
        assert independent_get_rfr_message_emoji_role(session) == expected_full_list
        assert independent_get_rfr_message_emoji_role(session,
                                                      2) == get_rfr_message_emoji_roles(2)
        assert independent_get_rfr_message_emoji_role(session,
                                                      1) == get_rfr_message_emoji_roles(1)

        # 2 roles 2 emojis 2 messages. Swapped
        msg3_id = dpyfactory.make_id()
        add_rfr_message(guild.id, channel.id, msg3_id)
        assert independent_get_guild_rfr_message(session) == [guild_rfr_message, (guild.id, channel.id, msg2_id, 2),
                                                              (guild.id, channel.id, msg3_id, 3)]
        guild_rfr_message_3 = independent_get_guild_rfr_message(session)[2]
        add_rfr_message_emoji_role(
            guild_rfr_message_3[3], fake_emoji_1, fake_role_id_2)
        add_rfr_message_emoji_role(
            guild_rfr_message_3[3], fake_emoji_2, fake_role_id_1)
        expected_full_list.extend([(guild_rfr_message_3[3], fake_emoji_1, fake_role_id_2),
                                   (guild_rfr_message_3[3], fake_emoji_2, fake_role_id_1)])
        assert independent_get_rfr_message_emoji_role(session) == expected_full_list
        assert independent_get_rfr_message_emoji_role(session,
                                                      3) == get_rfr_message_emoji_roles(3)
        assert [x[2] for x in independent_get_rfr_message_emoji_role(session, emoji_raw=fake_emoji_1)] == [
            get_rfr_reaction_role_by_emoji_str(1, fake_emoji_1),
            get_rfr_reaction_role_by_emoji_str(2, fake_emoji_1),
            get_rfr_reaction_role_by_emoji_str(3, fake_emoji_1)]
        assert [x[2] for x in independent_get_rfr_message_emoji_role(session, emoji_raw=fake_emoji_2)] == [
            get_rfr_reaction_role_by_emoji_str(1, fake_emoji_2),
            get_rfr_reaction_role_by_emoji_str(2, fake_emoji_2),
            get_rfr_reaction_role_by_emoji_str(3, fake_emoji_2)]
        # test deletion works from rfr message
        rfr_message_emoji_roles = independent_get_rfr_message_emoji_role(session, 3)
        remove_rfr_message(guild.id, channel.id, msg3_id)
        for row in rfr_message_emoji_roles:
            assert row not in independent_get_rfr_message_emoji_role(session
                                                                     ), independent_get_guild_rfr_message(session)
        # test deleting just emoji role combos
        rfr_message_emoji_roles = independent_get_rfr_message_emoji_role(session, 2)
        remove_rfr_message_emoji_roles(2)
        for row in rfr_message_emoji_roles:
            assert row not in independent_get_rfr_message_emoji_role(session
                                                                     ), independent_get_guild_rfr_message(session)
        # test deleteing specific
        rfr_message_emoji_roles = independent_get_rfr_message_emoji_role(session, 1)
        remove_rfr_message_emoji_role(
            1, emoji_raw=rfr_message_emoji_roles[0][1])
        assert (rfr_message_emoji_roles[0][0], rfr_message_emoji_roles[0][1],
                rfr_message_emoji_roles[0][2]) not in independent_get_rfr_message_emoji_role(session)
        remove_rfr_message_emoji_role(
            1, role_id=rfr_message_emoji_roles[1][2])
        assert (rfr_message_emoji_roles[1][0], rfr_message_emoji_roles[1][1],
                rfr_message_emoji_roles[1][2]) not in independent_get_rfr_message_emoji_role(session)


@pytest.mark.asyncio
async def test_rfr_db_functions_guild_rfr_required_roles():
    with session_manager() as session:
        guild: discord.Guild = dpytest.get_config().guilds[0]
        roles = []
        for i in range(50):
            role: discord.Role = testutils.fake_guild_role(guild)
            roles.append(role)
            add_guild_rfr_required_role(guild.id, role.id)
            assert [x[1] for x in independent_get_guild_rfr_required_role(session)] == [x.id for x in roles], i
            assert [x[1] for x in
                    independent_get_guild_rfr_required_role(session)] == get_guild_rfr_required_roles(
                guild.id), i

        while len(roles) > 0:
            role: discord.Role = roles.pop()
            remove_guild_rfr_required_role(guild.id, role.id)
            assert [x[1] for x in independent_get_guild_rfr_required_role(session)] == [x.id for x in roles], len(roles)
            assert [x[1] for x in
                    independent_get_guild_rfr_required_role(session)] == get_guild_rfr_required_roles(
                guild.id), len(roles)


@pytest.mark.parametrize("num_roles, num_required",
                         [(1, 1), (2, 1), (2, 2), (5, 1), (5, 2), (20, 5), (100, 20), (200, 20)])
@pytest.mark.asyncio
async def test_rfr_without_req_role(num_roles, num_required, rfr_cog):
    with session_manager() as session:
        config: dpytest.RunnerConfig = dpytest.get_config()
        test_guild: discord.Guild = config.guilds[0]

        r_list = []
        for i in range(num_roles):
            role = testutils.fake_guild_role(test_guild)
            r_list.append(role)
        required = random.sample(list(r_list), num_required)
        for r in required:
            add_guild_rfr_required_role(test_guild.id, r.id)
            assert independent_get_guild_rfr_required_role(session, test_guild.id, r.id) is not None

        member: discord.Member = await dpytest.member_join()
        await member.add_roles(*[r for r in r_list if r not in required])
        mem_roles = member.roles
        role_to_add = testutils.fake_guild_role(test_guild)

        # Create RFR message for test
        rfr_message = dpytest.back.make_message("FakeContent", config.client.user, test_guild.text_channels[0])
        add_rfr_message(test_guild.id, rfr_message.channel.id, rfr_message.id)
        assert get_rfr_message(test_guild.id, rfr_message.channel.id, rfr_message.id) is not None

        # Add emoji role combo to db
        _, _, _, er_id = get_rfr_message(test_guild.id, rfr_message.channel.id, rfr_message.id)
        react_emoji: str = testutils.fake_unicode_emoji()
        add_rfr_message_emoji_role(er_id, emoji.demojize(react_emoji), role_to_add.id)

        with mock.patch("koala.cogs.ReactForRole.get_role_member_info",
                        mock.AsyncMock(return_value=(member, role_to_add))):
            with mock.patch("discord.Member.add_roles", mock.AsyncMock()) as add_role_mock:
                await dpytest.add_reaction(member, rfr_message, react_emoji)
                assert all([m in member.roles for m in mem_roles])
                add_role_mock.assert_not_called()
                assert role_to_add not in member.roles


@pytest.mark.parametrize("num_roles, num_required",
                         [(1, 1), (2, 1), (2, 2), (5, 1), (5, 2), (20, 5), (100, 20), (200, 20)])
@pytest.mark.asyncio
async def test_rfr_with_req_role(num_roles, num_required, rfr_cog):
    with session_manager() as session:
        config: dpytest.RunnerConfig = dpytest.get_config()
        test_guild: discord.Guild = config.guilds[0]

        # Create RFR message for test
        rfr_message = dpytest.back.make_message("FakeContent", config.client.user, test_guild.text_channels[0])
        add_rfr_message(test_guild.id, rfr_message.channel.id, rfr_message.id)
        assert get_rfr_message(test_guild.id, rfr_message.channel.id, rfr_message.id) is not None

        r_list = []
        for i in range(num_roles):
            role = testutils.fake_guild_role(test_guild)
            r_list.append(role)
        required = random.sample(r_list, num_required)
        role_to_add = testutils.fake_guild_role(test_guild)

        # Add emoji role combo to db
        _, _, _, er_id = get_rfr_message(test_guild.id, rfr_message.channel.id, rfr_message.id)
        react_emoji: str = testutils.fake_unicode_emoji()
        add_rfr_message_emoji_role(er_id, emoji.demojize(react_emoji), role_to_add.id)

        for r in required:
            add_guild_rfr_required_role(test_guild.id, r.id)
            assert independent_get_guild_rfr_required_role(session, test_guild.id, r.id) is not None

        member: discord.Member = await dpytest.member_join()
        await member.add_roles(*(random.sample(r_list, random.randint(1, num_roles))))
        logger.debug(f"required = {[r.name for r in required]}, mem_roles pre-add are {[member.roles]}")
        if not any([r in required for r in member.roles]):
            x = random.choice(required)
            await member.add_roles(x)
            logger.debug(f"added role {x.name} to {member.display_name}")
        mem_roles = member.roles
        with mock.patch("koala.cogs.ReactForRole.get_role_member_info",
                        mock.AsyncMock(return_value=(member, role_to_add))):
            await dpytest.add_reaction(member, rfr_message, react_emoji)
            assert all([m in member.roles for m in mem_roles])
            assert role_to_add in member.roles
