#!/usr/bin/env python

"""
new Koala Bot database manager

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import os
# Libs
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

if os.name == 'nt':
    print("Windows Detected: Database Encryption Disabled")
    import sqlite3
else:
    print("Linux Detected: Database Encryption Enabled")
    from pysqlcipher3 import dbapi2 as sqlite3

from sqlalchemy import select, delete, and_, create_engine, func as sql_func
from sqlalchemy.orm import sessionmaker

# Own modules
from koala.env import DB_KEY, ENCRYPTED_DB
from koala.models import mapper_registry, KoalaExtensions, GuildExtensions
from koala.utils import get_arg_config_path, format_config_path
from koala.log import logger

# Constants

# Variables


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


def _get_sql_url(db_path, encrypted: bool, db_key=None):
    if encrypted:
        return "sqlite+pysqlcipher://:x'" + db_key + "'@/" + db_path
    else:
        return "sqlite:///" + db_path


CONFIG_DIR = get_arg_config_path()
DATABASE_PATH = format_config_path(CONFIG_DIR, "Koala.db" if ENCRYPTED_DB else "windows_Koala.db")
logger.debug("Database Path: "+DATABASE_PATH)
engine = create_engine(_get_sql_url(db_path=DATABASE_PATH,
                                    encrypted=ENCRYPTED_DB,
                                    db_key=DB_KEY), module=sqlite3)
Session = sessionmaker(future=True)
Session.configure(bind=engine)


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


def setup():
    """
    Creates the database and tables
    """
    __create_db(DATABASE_PATH)
    __create_tables()


def __create_db(file_path):
    """
    Creates the database, with correct permissions on unix
    :param file_path: The file path of the database
    """
    Path(get_arg_config_path()).mkdir(exist_ok=True)
    Path(file_path).touch()
    if ENCRYPTED_DB:
        os.system("chown www-data "+file_path)
        os.system("chmod 777 "+file_path)


def __create_tables():
    """
    Creates all tables currently in the metadata of Base
    """
    mapper_registry.metadata.create_all(engine, mapper_registry.metadata.tables.values(), checkfirst=True)


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


def clear_all_tables():
    """
    Clears all the data from the given tables
    """
    with session_manager() as session:
        for table in reversed(mapper_registry.metadata.sorted_tables):
            print('Clear table %s' % table)
            session.execute(table.delete())
        session.commit()


setup()
