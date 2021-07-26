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

# Own modules
import KoalaBot
from cogs import Voting
from utils import KoalaDBManager


class Fake:
    def __getattr__(self, item):
        setattr(self, item, Fake())
        return getattr(self, item)


ctx = Fake()
ctx.author.id = 1234
ctx.guild.id = 4567
cog = None
db_manager = KoalaDBManager.KoalaDBManager("votingTest.db", KoalaBot.DB_KEY, KoalaBot.config_dir)
db_manager.create_base_tables()
vote_manager = None


def populate_vote_tables():
    db_manager.db_execute_commit("INSERT INTO Votes VALUES (?, ?, ?, ?, ?, ?, ?)",
                                 (111, 222, 333, "Test Vote 1", None, None, None))
    db_manager.db_execute_commit("INSERT INTO VoteTargetRoles VALUES (?, ?)", (111, 999))
    db_manager.db_execute_commit("INSERT INTO VoteOptions VALUES (?, ?, ?, ?)", (111, 888, "vote1opt", "vote1body"))
    db_manager.db_execute_commit("INSERT INTO VoteOptions VALUES (?, ?, ?, ?)", (111, 887, "vote1opt2", "vote1body"))
    db_manager.db_execute_commit("INSERT INTO VoteSent VALUES (?, ?, ?)", (111, 777, 666))
    db_manager.db_execute_commit("INSERT INTO Votes VALUES (?, ?, ?, ?, ?, ?, ?)",
                                 (112, 223, 334, "Test Vote 2", 555, 666, None))
    db_manager.db_execute_commit("INSERT INTO VoteOptions VALUES (?, ?, ?, ?)", (112, 888, "vote1opt", "vote1body"))



@pytest.fixture(autouse=True)
def cog(bot):
    global vote_manager
    cog = Voting.Voting(bot, db_manager)
    db_manager.db_execute_commit("DROP TABLE Votes")
    db_manager.db_execute_commit("DROP TABLE VoteTargetRoles")
    db_manager.db_execute_commit("DROP TABLE VoteOptions")
    db_manager.db_execute_commit("DROP TABLE VoteSent")
    db_manager.insert_extension("Vote", 0, True, True)
    vote_manager = Voting.VoteManager(db_manager)
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
    config = dpytest.get_config()
    guild = config.guilds[0]
    await dpytest.message(f"{KoalaBot.COMMAND_PREFIX}vote create Test Vote")
    assert dpytest.verify().message().content(f"Vote titled `Test Vote` created for guild {guild.name}. Use `{KoalaBot.COMMAND_PREFIX}help vote` to see how to configure it.")
    in_db = db_manager.db_execute_select("SELECT * FROM Votes")[0]
    assert in_db
    assert in_db[1] == guild.members[0].id
    assert in_db[2] == guild.id


@pytest.mark.asyncio
async def test_discord_create_vote_wrong():
    config = dpytest.get_config()
    guild = config.guilds[0]
    db_manager.db_execute_commit("INSERT INTO Votes VALUES (?, ?, ?, ?, ?, ?, ?)", (111, guild.members[0].id, guild.id, "Test Vote", None, None, None))
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
    opt = Voting.Option("test", "option", 123456789)
    assert opt.id == 123456789
    assert opt.head == "test"
    assert opt.body == "option"


def test_votemanager_generate_opt_id():
    db_manager.db_execute_commit("INSERT INTO VoteOptions VALUES (?, ?, ?, ?)", (123, 100000000000000001, "test", "option"))
    opt_id = vote_manager.generate_unique_opt_id()
    assert opt_id != 100000000000000001


def test_votemanager_load_from_db():
    populate_vote_tables()
    vote_manager.load_from_db()
    assert vote_manager.vote_lookup[(222, "Test Vote 1")] == 111
    vote = vote_manager.sent_votes[111]
    assert vote.target_roles == [999]
    assert vote.options[0].id == 888
    assert vote.options[0].head == "vote1opt"
    assert vote.options[0].body == "vote1body"
    assert vote.sent_to[777] == 666


def test_votemanager_get_vote_from_id():
    populate_vote_tables()
    vote_manager.load_from_db()
    vote = vote_manager.get_vote_from_id(111)
    assert vote.id == 111
    assert vote.options[0].id == 888
    assert vote.title == "Test Vote 1"


def test_votemanager_get_configuring_vote():
    populate_vote_tables()
    vote_manager.load_from_db()
    vote = vote_manager.get_configuring_vote(223)
    assert vote.title == "Test Vote 2"


def test_votemanager_has_active_vote():
    populate_vote_tables()
    vote_manager.load_from_db()
    assert vote_manager.has_active_vote(223)


def test_votemanager_create_vote():
    vote = vote_manager.create_vote(123, 456, "Create Vote Test")
    assert vote.title == "Create Vote Test"
    in_db = db_manager.db_execute_select("SELECT * FROM Votes WHERE author_id=? AND title=?", (123, "Create Vote Test"))
    assert in_db


def test_votemanager_cancel_sent_vote():
    populate_vote_tables()
    vote_manager.load_from_db()
    vote_manager.cancel_sent_vote(111)
    assert 111 not in vote_manager.sent_votes.keys()
    in_db = db_manager.db_execute_select("SELECT * FROM Votes WHERE vote_id=?", (111,))
    assert not in_db


def test_votemanager_cancel_configuring_vote():
    populate_vote_tables()
    vote_manager.load_from_db()
    vote_manager.cancel_configuring_vote(223)
    assert 223 not in vote_manager.configuring_votes.keys()
    in_db = db_manager.db_execute_select("SELECT * FROM Votes WHERE vote_id=?", (112,))
    assert not in_db


def test_votemanager_sent_to():
    populate_vote_tables()
    vote_manager.load_from_db()
    assert vote_manager.was_sent_to(666)


def test_vote_is_ready():
    vote = Voting.Vote(111, "Test Vote", 222, 333, db_manager)
    vote.add_option(Voting.Option(111, "head", "body"))
    assert not vote.is_ready()
    vote.add_option(Voting.Option(122, "head", "body"))
    assert vote.is_ready()


def test_vote_add_role():
    vote = Voting.Vote(111, "Test Vote", 222, 333, db_manager)
    vote.add_role(777)
    assert 777 in vote.target_roles
    in_db = db_manager.db_execute_select("SELECT * FROM VoteTargetRoles WHERE vote_id=? AND role_id=?", (111, 777))
    assert in_db


def test_vote_remove_role():
    vote = Voting.Vote(111, "Test Vote", 222, 333, db_manager)
    vote.add_role(777)
    vote.remove_role(777)
    assert 777 not in vote.target_roles
    in_db = db_manager.db_execute_select("SELECT * FROM VoteTargetRoles WHERE vote_id=? AND role_id=?", (111, 777))
    assert not in_db


def test_vote_set_chair():
    vote = vote_manager.create_vote(111, 222, "Set Chair Vote Test")
    vote.set_chair(555)
    assert vote.chair == 555
    in_db = db_manager.db_execute_select("SELECT * FROM Votes WHERE vote_id=? AND chair_id=?", (vote.id, 555))
    assert in_db
    vote.set_chair()
    assert not vote.chair
    in_db = db_manager.db_execute_select("SELECT * FROM Votes WHERE vote_id=?", (vote.id,))
    assert not in_db[0][4]


def test_vote_set_vc():
    vote = vote_manager.create_vote(111, 222, "Set Chair Vote Test")
    vote.set_vc(555)
    assert vote.target_voice_channel == 555
    in_db = db_manager.db_execute_select("SELECT * FROM Votes WHERE vote_id=? AND voice_id=?", (vote.id, 555))
    assert in_db
    vote.set_vc()
    assert not vote.target_voice_channel
    in_db = db_manager.db_execute_select("SELECT * FROM Votes WHERE vote_id=?", (vote.id,))
    assert not in_db[0][5]


def test_vote_add_option():
    vote = vote_manager.create_vote(111, 222, "Add Option Test")
    vote.add_option(Voting.Option("head", "body", 123))
    assert vote.options[0].head == "head"
    assert vote.options[0].body == "body"
    in_db = db_manager.db_execute_select("SELECT * FROM VoteOptions WHERE opt_id=?", (123,))
    assert in_db


def test_vote_remove_option():
    vote = vote_manager.create_vote(111, 222, "Remove Option Test")
    vote.add_option(Voting.Option("head", "body", 123))
    vote.remove_option(0)
    in_db = db_manager.db_execute_select("SELECT * FROM VoteOptions WHERE opt_id=?", (123,))
    assert not in_db


def test_vote_register_sent():
    vote = vote_manager.create_vote(111, 222, "Register Sent Test")
    vote.register_sent(555, 666)
    assert vote.sent_to[555] == 666
    in_db = db_manager.db_execute_select("SELECT * FROM VoteSent WHERE vote_receiver_message=?", (666,))
    assert in_db


def test_two_way():
    def test_asserts(f, *args, **kwargs):
        try:
            f(*args, **kwargs)
        except AssertionError:
            return
        raise AssertionError

    # test internal asserts don't false positive
    t = Voting.TwoWay({1: 2, 3: 4})
    t2 = Voting.TwoWay({1: 2, 2: 1, 4: 3})
    assert t == t2

    # test an invalid dict cannot be made
    test_asserts(Voting.TwoWay, {1: 2, 2: 3})

    def ta2():
        t = Voting.TwoWay()
        t[1] = 2
        t[2] = 3
        test_asserts(ta2)
