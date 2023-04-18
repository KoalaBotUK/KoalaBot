#!/usr/bin/env python

"""
new Koala Bot database manager

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
# Libs
from contextlib import contextmanager
from functools import wraps

from sqlalchemy import select, delete, and_, create_engine, VARCHAR, func as sql_func
from sqlalchemy.orm import sessionmaker

# Own modules
from .enums import DatabaseType
from koala.env import DB_URL, DB_TYPE
from koala.models import mapper_registry, KoalaExtensions, GuildExtensions
from koala.log import logger


# Constants

# Variables
engine = create_engine(DB_URL, future=True, pool_size=20, pool_recycle=3600)
Session = sessionmaker(future=True)
Session.configure(bind=engine)


def assign_session(func):

    @wraps(func)
    def with_session(*args, **kwargs):
        if not kwargs.get("session"):
            with session_manager() as session:
                kwargs["session"] = session
                return func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    return with_session


@contextmanager
def session_manager():
    """
    Provide a transactional scope around a series of operations
    """
    session = Session()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def __create_sqlite_tables():
    """
    Creates all tables currently in the metadata of Base
    """
    logger.debug("Creating database tables for SQLite")
    tables = mapper_registry.metadata.tables.values()
    for table in tables:
        for column in table.columns:
            existing_type = column.type
            if type(existing_type) == VARCHAR:
                existing_type.collation = None
                column.type = existing_type
    mapper_registry.metadata.create_all(engine, tables, checkfirst=True)


def insert_extension(extension_id: str, subscription_required: int, available: bool, enabled: bool):
    """
    Inserts a Koala Extension into the KoalaExtensions table

    :param extension_id: The unique extension ID/ name
    :param subscription_required: The required subscription level to unlock this extension
    :param available: Is available to be enabled by the public
        (false for if a special extension is to be enabled in one server only by the devs)
    :param enabled: Is currently enabled and running
        (false if down for maintenance)
    """
    with session_manager() as session:
        extension: KoalaExtensions = session.execute(select(KoalaExtensions)
                                                     .where(KoalaExtensions.extension_id == extension_id)
                                                     ).scalars().one_or_none()
        if extension:
            extension.subscription_required = subscription_required
            extension.available = available
            extension.enabled = enabled
        else:
            session.add(KoalaExtensions(extension_id=extension_id,
                                        subscription_required=subscription_required,
                                        available=available,
                                        enabled=enabled))
        session.commit()


def extension_enabled(guild_id, extension_id: str):
    """
    Check if a given extension is enabled in a specific guild

    :param guild_id: Discord guild ID for a given server
    :param extension_id: The Koala extension ID
    """
    with session_manager() as session:
        result = session.execute(select(GuildExtensions.extension_id)
                                 .where(GuildExtensions.guild_id == guild_id)
                                 ).scalars().all()
    return "All" in result or extension_id in result


@assign_session
def give_guild_extension(guild_id, extension_id: str, session: Session):
    """
    Give a guild the given Koala extension

    :param guild_id: Discord guild ID for a given server
    :param extension_id: The Koala extension ID
    :param session: sqlalchemy Session

    :raises NotImplementedError: extension_id doesnt exist
    """
    extension_exists = extension_id == "All" or session.execute(
            select(sql_func.count(KoalaExtensions.extension_id))
            .filter_by(extension_id=extension_id, available=1)).scalars().one() > 0

    if extension_exists:
        if session.execute(
                select(GuildExtensions)
                .filter_by(extension_id=extension_id, guild_id=guild_id)).one_or_none() is None:
            session.add(GuildExtensions(extension_id=extension_id, guild_id=guild_id))
            session.commit()
    else:
        raise NotImplementedError(f"{extension_id} is not a valid extension")


@assign_session
def remove_guild_extension(guild_id, extension_id: str, session: Session):
    """
    Remove a given Koala extension from a guild

    :param guild_id: Discord guild ID for a given server
    :param extension_id: The Koala extension ID
    :param session: sqlalchemy Session
    """
    session.execute(delete(GuildExtensions).filter_by(extension_id=extension_id, guild_id=guild_id))
    session.commit()


@assign_session  # fallback assign session
def get_enabled_guild_extensions(guild_id: int, session: Session):
    """
    Gets a list of extensions IDs that are enabled in a server

    :param guild_id: Discord guild ID for a given server
    :param session: sqlalchemy Session
    """
    sql_select_enabled = select(GuildExtensions.extension_id)\
        .join(KoalaExtensions, GuildExtensions.extension_id == KoalaExtensions.extension_id)\
        .where(
        and_(
            GuildExtensions.guild_id == guild_id,
            KoalaExtensions.available == 1))
    return session.execute(sql_select_enabled)\
        .scalars(GuildExtensions.extension_id).all()    # todo: test if works


@assign_session
def get_all_available_guild_extensions(guild_id: int, session: Session):
    """
    Gets all available guild extensions for a given guild

    todo: restrict with rules of subscriptions & enabled state

    :param guild_id: Discord guild ID for a given server
    :param session: sqlalchemy Session
    """
    sql_select_all = select(KoalaExtensions.extension_id).filter_by(available=1).distinct()
    return session.execute(sql_select_all)\
        .scalars(KoalaExtensions.extension_id).all()    # todo: test if works
        # [extension.extension_id for extension in session.execute(sql_select_all).all()]


def fetch_all_tables():
    """
    Fetches all table names within the database
    """
    with session_manager() as session:
        if DB_TYPE == DatabaseType.SQLITE:
            return [table.name for table in
                    session.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;").all()]
        else:
            return [row[0] for row in session.execute("SHOW Tables;").all()]


def clear_all_tables(tables):
    """
    Clears al the data from the given tables

    :param tables: a list of all tables to be cleared
    """
    with session_manager() as session:
        for table in tables:
            session.execute('DELETE FROM ' + table + ';')
        session.commit()
