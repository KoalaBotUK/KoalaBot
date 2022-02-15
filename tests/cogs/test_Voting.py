#!/usr/bin/env python
"""
Testing KoalaBot VoteCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import asyncio
# Libs
from unittest import TestCase

import discord
import discord.ext.test as dpytest
import mock
import pytest
from discord.ext import commands
from sqlalchemy import select, delete

# Own modules
import KoalaBot
from koala.utils import KoalaDBManager
from koala.utils.KoalaUtils import format_config_path
from koala.env import CONFIG_PATH
from koala.db import setup, session_manager
from koala.cogs import Voting
from koala.cogs.voting.models import Votes, VoteSent, VoteOptions, VoteTargetRoles
from koala.cogs.voting.db import VoteManager
from koala.cogs.voting.option import Option
from koala.cogs.voting.two_way import TwoWay
from koala.cogs.voting.vote import Vote


class Fake:
    def __getattr__(self, item):
        setattr(self, item, Fake())
        return getattr(self, item)


ctx = Fake()
ctx.author.id = 1234
ctx.guild.id = 4567
cog = None
db_manager = KoalaBot.database_manager
db_manager.create_base_tables()
vote_manager = VoteManager(db_manager)


def populate_vote_tables(session):
    session.add(Votes(vote_id=111, author_id=222, guild_id=333, title="Test Vote 1"))
    session.add(VoteTargetRoles(vote_id=111, role_id=999))
    session.add(VoteOptions(vote_id=111, opt_id=888, option_title="vote1opt", option_desc="vote1body"))
    session.add(VoteOptions(vote_id=111, opt_id=887, option_title="vote1opt2", option_desc="vote1body"))
    session.add(VoteSent(vote_id=111, vote_receiver_id=777, vote_receiver_message=666))
    session.add(Votes(vote_id=112, author_id=223, guild_id=334, title="Test Vote 2", chair_id=555, voice_id=666))
    session.add(VoteOptions(vote_id=112, opt_id=888, option_title="vote1opt", option_desc="vote1body"))
    session.commit()

@pytest.fixture(autouse=True)
def cog(bot):
    with session_manager() as session:
        cog = Voting(bot, db_manager)
        session.execute(delete(Votes))
        session.execute(delete(VoteTargetRoles))
        session.execute(delete(VoteOptions))
        session.execute(delete(VoteSent))
        session.commit()
        db_manager.insert_extension("Vote", 0, True, True)
        bot.add_cog(cog)
        dpytest.configure(bot)
        print("Tests starting")
        return cog


@pytest.fixture(scope='session', autouse=True)
def setup_is_dpytest():
    KoalaBot.is_dpytest = True
    yield
    KoalaBot.is_dpytest = False


@pytest.mark.asyncio
async def test_discord_create_vote():
    with session_manager() as session:
        config = dpytest.get_config()
        guild = config.guilds[0]
        await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote create Test Vote")
        assert dpytest.verify().message().content(f"Vote titled `Test Vote` created for guild {guild.name}. Use `{KoalaBot.COMMAND_PREFIX}help vote` to see how to configure it.")
        in_db = session.execute(select(Votes.author_id, Votes.guild_id)).first()
        assert in_db
        assert in_db[0] == guild.members[0].id
        assert in_db[1] == guild.id


@pytest.mark.asyncio
async def test_discord_create_vote_wrong():
    with session_manager() as session:
        config = dpytest.get_config()
        guild = config.guilds[0]
        session.add(Votes(vote_id=111, author_id=guild.members[0].id, guild_id=guild.id, title="Test Vote"))
        session.commit()
        await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote create Test Vote")
        assert dpytest.verify().message().content("You already have a vote with title Test Vote sent!")
        await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote create aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        assert dpytest.verify().message().content("Title too long")
        await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote create Test Vote 2")
        assert dpytest.verify().message().content(
            f"Vote titled `Test Vote 2` created for guild {guild.name}. Use `{KoalaBot.COMMAND_PREFIX}help vote` to see how to configure it.")
        await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote create Test Vote 3")
        assert dpytest.verify().message().content(f"You already have an active vote in {guild.name}. Please send that with `{KoalaBot.COMMAND_PREFIX}vote send` before creating a new one.")


@pytest.mark.asyncio
async def test_discord_vote_add_and_remove_role(cog):
    config = dpytest.get_config()
    guild = config.guilds[0]
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote create Test Vote")
    assert dpytest.verify().message().content(
        f"Vote titled `Test Vote` created for guild {guild.name}. Use `{KoalaBot.COMMAND_PREFIX}help vote` to see how to configure it.")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote addRole {guild.roles[0].id}")
    assert dpytest.verify().message().content(f"Vote will be sent to those with the {guild.roles[0].name} role")
    vote = cog.vote_manager.get_configuring_vote(guild.members[0].id)
    assert guild.roles[0].id in vote.target_roles
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote removeRole {guild.roles[0].id}")
    assert dpytest.verify().message().content(f"Vote will no longer be sent to those with the {guild.roles[0].name} role")
    assert guild.roles[0].id not in vote.target_roles


@pytest.mark.asyncio
async def test_discord_set_chair():
    config = dpytest.get_config()
    guild = config.guilds[0]
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote create Test Vote")
    assert dpytest.verify().message().content(
        f"Vote titled `Test Vote` created for guild {guild.name}. Use `{KoalaBot.COMMAND_PREFIX}help vote` to see how to configure it.")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote setChair {guild.members[0].id}")
    assert dpytest.verify().message().content(f"You have been selected as the chair for vote titled Test Vote")
    assert dpytest.verify().message().content(f"Set chair to {guild.members[0].name}")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote setChair")
    assert dpytest.verify().message().content("Results will be sent to the channel vote is closed in")

@pytest.mark.asyncio
async def test_discord_add_remove_option():
    config = dpytest.get_config()
    guild = config.guilds[0]
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote create Test Vote")
    assert dpytest.verify().message().content(
        f"Vote titled `Test Vote` created for guild {guild.name}. Use `{KoalaBot.COMMAND_PREFIX}help vote` to see how to configure it.")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote addOption test+test")
    assert dpytest.verify().message().content("Option test with description test added to vote")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote addOption testtest")
    assert dpytest.verify().message().content("Example usage: k!vote addOption option title+option description")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote removeOption 1")
    assert dpytest.verify().message().content("Option number 1 removed")


@pytest.mark.asyncio
async def test_discord_cancel_vote():
    config = dpytest.get_config()
    guild = config.guilds[0]
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote create Test Vote")
    assert dpytest.verify().message().content(
        f"Vote titled `Test Vote` created for guild {guild.name}. Use `{KoalaBot.COMMAND_PREFIX}help vote` to see how to configure it.")
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote cancel Test Vote")
    assert dpytest.verify().message().content("Vote Test Vote has been cancelled.")


def test_option():
    opt = Option("test", "option", 123456789)
    assert opt.id == 123456789
    assert opt.head == "test"
    assert opt.body == "option"


def test_votemanager_generate_opt_id():
    with session_manager() as session:
        session.add(VoteOptions(vote_id=123, opt_id=100000000000000001, option_title="test", option_desc="option"))
        session.commit()
        opt_id = vote_manager.generate_unique_opt_id()
        assert opt_id != 100000000000000001


def test_votemanager_load_from_db():
    with session_manager() as session:
        populate_vote_tables(session)
        vote_manager.load_from_db()
        assert vote_manager.vote_lookup[(222, "Test Vote 1")] == 111
        vote = vote_manager.sent_votes[111]
        assert vote.target_roles == [999]
        assert vote.options[1].id == 888
        assert vote.options[1].head == "vote1opt"
        assert vote.options[1].body == "vote1body"
        assert vote.sent_to[777] == 666


def test_votemanager_get_vote_from_id():
    with session_manager() as session:
        populate_vote_tables(session)
        vote_manager.load_from_db()
        vote = vote_manager.get_vote_from_id(111)
        assert vote.id == 111
        assert vote.options[1].id == 888
        assert vote.title == "Test Vote 1"


def test_votemanager_get_configuring_vote():
    with session_manager() as session:
        populate_vote_tables(session)
        vote_manager.load_from_db()
        vote = vote_manager.get_configuring_vote(223)
        assert vote.title == "Test Vote 2"


def test_votemanager_has_active_vote():
    with session_manager() as session:
        populate_vote_tables(session)
        vote_manager.load_from_db()
        assert vote_manager.has_active_vote(223)


def test_votemanager_create_vote():
    with session_manager() as session:
        vote = vote_manager.create_vote(123, 456, "Create Vote Test")
        assert vote.title == "Create Vote Test"
        in_db = session.execute(select(Votes).filter_by(author_id=123, title="Create Vote Test")).all()
        assert in_db


def test_votemanager_cancel_sent_vote():
    with session_manager() as session:
        populate_vote_tables(session)
        vote_manager.load_from_db()
        vote_manager.cancel_sent_vote(111)
        assert 111 not in vote_manager.sent_votes.keys()
        in_db = session.execute(select(Votes).filter_by(vote_id=111)).all()
        assert not in_db


def test_votemanager_cancel_configuring_vote():
    with session_manager() as session:
        populate_vote_tables(session)
        vote_manager.load_from_db()
        vote_manager.cancel_configuring_vote(223)
        assert 223 not in vote_manager.configuring_votes.keys()
        in_db = session.execute(select(Votes).filter_by(vote_id=112)).all()
        assert not in_db


def test_votemanager_sent_to():
    with session_manager() as session:
        populate_vote_tables(session)
        vote_manager.load_from_db()
        assert vote_manager.was_sent_to(666)


def test_vote_is_ready():
    vote = Vote(111, "Test Vote", 222, 333, db_manager)
    vote.add_option(Option(111, "head", "body"))
    assert not vote.is_ready()
    vote.add_option(Option(122, "head", "body"))
    assert vote.is_ready()


def test_vote_add_role():
    with session_manager() as session:
        vote = Vote(111, "Test Vote", 222, 333, db_manager)
        vote.add_role(777)
        assert 777 in vote.target_roles
        in_db = session.execute(select(VoteTargetRoles).filter_by(vote_id=111, role_id=777))
        assert in_db


def test_vote_remove_role():
    with session_manager() as session:
        vote = Vote(111, "Test Vote", 222, 333, db_manager)
        vote.add_role(777)
        vote.remove_role(777)
        assert 777 not in vote.target_roles
        in_db = session.execute(select(VoteTargetRoles).filter_by(vote_id=111, role_id=777)).all()
        assert not in_db


def test_vote_set_chair():
    with session_manager() as session:
        vote = vote_manager.create_vote(111, 222, "Set Chair Vote Test")
        vote.set_chair(555)
        assert vote.chair == 555
        in_db = session.execute(select(Votes).filter_by(vote_id=vote.id, chair_id=555)).all()
        assert in_db
        vote.set_chair()
        assert not vote.chair
        in_db = session.execute(select(Votes).filter_by(vote_id=vote.id)).all()
        assert not in_db[0][4]


def test_vote_set_vc():
    with session_manager() as session:
        vote = vote_manager.create_vote(111, 222, "Set Chair Vote Test")
        vote.set_vc(555)
        assert vote.target_voice_channel == 555
        in_db = session.execute(select(Votes).filter_by(vote_id=vote.id, voice_id=555)).all()
        assert in_db
        vote.set_vc()
        assert not vote.target_voice_channel
        in_db = session.execute(select(Votes).filter_by(vote_id=vote.id)).scalar()
        assert not in_db.voice_id


def test_vote_add_option():
    with session_manager() as session:
        vote = vote_manager.create_vote(111, 222, "Add Option Test")
        vote.add_option(Option("head", "body", 123))
        assert vote.options[0].head == "head"
        assert vote.options[0].body == "body"
        in_db = session.execute(select(VoteOptions).filter_by(opt_id=123)).all()
        assert in_db


def test_vote_remove_option():
    with session_manager() as session:
        vote = vote_manager.create_vote(111, 222, "Remove Option Test")
        vote.add_option(Option("head", "body", 123))
        vote.remove_option(0)
        in_db = session.execute(select(VoteOptions).filter_by(opt_id=123)).all()
        assert not in_db


def test_vote_register_sent():
    with session_manager() as session:
        vote = vote_manager.create_vote(111, 222, "Register Sent Test")
        vote.register_sent(555, 666)
        assert vote.sent_to[555] == 666
        in_db = session.execute(select(VoteSent).filter_by(vote_receiver_message=666)).all()
        assert in_db


def test_two_way():
    def test_asserts(f, *args, **kwargs):
        try:
            f(*args, **kwargs)
        except AssertionError:
            return
        raise AssertionError

    # test internal asserts don't false positive
    t = TwoWay({1: 2, 3: 4})
    t2 = TwoWay({1: 2, 2: 1, 4: 3})
    assert t == t2

    # test an invalid dict cannot be made
    test_asserts(TwoWay, {1: 2, 2: 3})

    def ta2():
        t = TwoWay()
        t[1] = 2
        t[2] = 3
        test_asserts(ta2)
