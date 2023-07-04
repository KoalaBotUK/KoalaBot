#!/usr/bin/env python
"""
Testing KoalaBot VoteCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
from sqlalchemy import select

# Own modules
from koala.cogs.voting.models import Votes, VoteSent, VoteOptions
from koala.cogs.voting.option import Option
from koala.db import session_manager
from .utils import populate_vote_tables, vote_manager


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
        vote = vote_manager.create_vote(123, 456, "Create Vote Test", session)
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


def test_vote_set_chair():
    with session_manager() as session:
        vote = vote_manager.create_vote(111, 222, "Set Chair Vote Test", session)
        vote.set_chair(555)
        assert vote.chair == 555
        in_db = session.execute(select(Votes).filter_by(vote_id=vote.id, chair_id=555)).all()
        assert in_db
        vote.set_chair()
        assert not vote.chair
        session.expire(in_db)
        in_db = session.execute(select(Votes).filter_by(vote_id=vote.id)).scalar()
        assert not in_db.chair_id == 555


def test_vote_set_vc():
    with session_manager() as session:
        vote = vote_manager.create_vote(111, 222, "Set Chair Vote Test", session)
        vote.set_vc(555)
        assert vote.target_voice_channel == 555
        in_db = session.execute(select(Votes).filter_by(vote_id=vote.id)).scalar()
        assert in_db.voice_id == 555
        vote.set_vc()
        assert not vote.target_voice_channel
        session.expire(in_db)
        in_db = session.execute(select(Votes).filter_by(vote_id=vote.id)).scalar()
        assert not in_db.voice_id == 555


def test_vote_add_option():
    with session_manager() as session:
        vote = vote_manager.create_vote(111, 222, "Add Option Test", session)
        vote.add_option(Option("head", "body", 123))
        assert vote.options[0].head == "head"
        assert vote.options[0].body == "body"
        in_db = session.execute(select(VoteOptions).filter_by(opt_id=123)).all()
        assert in_db


def test_vote_remove_option():
    with session_manager() as session:
        vote = vote_manager.create_vote(111, 222, "Remove Option Test", session)
        vote.add_option(Option("head", "body", 123))
        vote.remove_option(0)
        in_db = session.execute(select(VoteOptions).filter_by(opt_id=123)).all()
        assert not in_db


def test_vote_register_sent():
    with session_manager() as session:
        vote = vote_manager.create_vote(111, 222, "Register Sent Test", session)
        vote.register_sent(555, 666)
        assert vote.sent_to[555] == 666
        in_db = session.execute(select(VoteSent).filter_by(vote_receiver_message=666)).all()
        assert in_db
