#!/usr/bin/env python

# Futures
# Built-in/Generic Imports
# Libs
import sqlalchemy.orm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

# Own modules
from koala.cogs.verification import errors
from koala.cogs.verification.models import VerifyBlacklist
from koala.db import assign_session

# Constants
# Variables


@assign_session
def add_to_blacklist(user_id, role_id, suffix, session: sqlalchemy.orm.Session):
    blacklisted = VerifyBlacklist(user_id=user_id, role_id=role_id, email_suffix=suffix)
    try:
        session.add(blacklisted)
        session.commit()
    except IntegrityError:
        raise errors.VerifyException("This user verification is already blacklisted.")
    return blacklisted


@assign_session
def remove_from_blacklist(user_id, role_id, suffix, session: sqlalchemy.orm.Session):
    blacklisted = session.execute(select(VerifyBlacklist)
                                  .filter_by(user_id=user_id, role_id=role_id, email_suffix=suffix)).scalar()
    if not blacklisted:
        raise errors.VerifyException("This user verification blacklist doesn't exist.")
    session.delete(blacklisted)
    session.commit()
    return blacklisted
