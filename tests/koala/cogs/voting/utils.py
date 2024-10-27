#!/usr/bin/env python
"""
Testing KoalaBot VoteCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs

# Own modules
from koala.cogs.voting.db import VoteManager
from koala.cogs.voting.models import Votes, VoteSent, VoteOptions, VoteTargetRoles


class Fake:
    def __getattr__(self, item):
        setattr(self, item, Fake())
        return getattr(self, item)


ctx = Fake()
ctx.author.id = 1234
ctx.guild.id = 4567
cog = None
vote_manager = VoteManager()


def populate_vote_tables(session):
    session.add(Votes(vote_id=111, author_id=222, guild_id=333, title="Test Vote 1"))
    session.add(VoteTargetRoles(vote_id=111, role_id=999))
    session.add(VoteOptions(vote_id=111, opt_id=888, option_title="vote1opt", option_desc="vote1body"))
    session.add(VoteOptions(vote_id=111, opt_id=887, option_title="vote1opt2", option_desc="vote1body"))
    session.add(VoteSent(vote_id=111, vote_receiver_id=777, vote_receiver_message=666))
    session.add(Votes(vote_id=112, author_id=223, guild_id=334, title="Test Vote 2", chair_id=555, voice_id=666))
    session.add(VoteOptions(vote_id=112, opt_id=888, option_title="vote1opt", option_desc="vote1body"))
    session.commit()
