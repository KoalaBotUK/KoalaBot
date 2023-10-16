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
from koala.cogs.voting.models import VoteTargetRoles
from koala.cogs.voting.option import Option
from koala.cogs.voting.vote import Vote
from koala.db import session_manager


def test_vote_is_ready():
    vote = Vote(111, "Test Vote", 222, 333)
    vote.add_option(Option("head", "body", 111))
    assert not vote.is_ready()
    vote.add_option(Option("head", "body", 122))
    assert vote.is_ready()


def test_vote_add_role():
    with session_manager() as session:
        vote = Vote(111, "Test Vote", 222, 333)
        vote.add_role(777, session=session)
        assert 777 in vote.target_roles
        in_db = session.execute(select(VoteTargetRoles).filter_by(vote_id=111, role_id=777))
        assert in_db


def test_vote_remove_role():
    with session_manager() as session:
        vote = Vote(111, "Test Vote", 222, 333)
        vote.add_role(777, session=session)
        vote.remove_role(777, session=session)
        assert 777 not in vote.target_roles
        in_db = session.execute(select(VoteTargetRoles).filter_by(vote_id=111, role_id=777)).all()
        assert not in_db
