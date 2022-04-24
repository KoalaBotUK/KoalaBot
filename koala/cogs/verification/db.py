import sqlalchemy.orm
from sqlalchemy import select

from koala.cogs.verification.models import VerifyBlacklist
from koala.db import assign_session


@assign_session
def add_to_blacklist(user_id, role_id, suffix, session: sqlalchemy.orm.Session):
    blacklisted = VerifyBlacklist(user_id=user_id, role_id=role_id, email=suffix)
    session.add(blacklisted)
    session.commit()
    return blacklisted


@assign_session
def remove_from_blacklist(user_id, role_id, suffix, session: sqlalchemy.orm.Session):
    blacklisted = session.execute(select(VerifyBlacklist).filter_by(user_id=user_id, role_id=role_id, email=suffix))
    session.delete(blacklisted)
    session.commit()
    return blacklisted
