#!/usr/bin/env python
"""
Testing KoalaBot VoteCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import pytest
from sqlalchemy import delete

# Own modules
from koala.cogs.voting.models import Votes, VoteSent, VoteOptions, VoteTargetRoles
from koala.db import session_manager


@pytest.fixture(autouse=True)
def clear_tables():
    with session_manager() as session:
        session.execute(delete(Votes))
        session.execute(delete(VoteTargetRoles))
        session.execute(delete(VoteOptions))
        session.execute(delete(VoteSent))
        session.commit()
