#!/usr/bin/env python
"""
Testing KoalaBot IntroCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

import asyncio

# Libs
import discord.ext.test.factories as dpyfactory

# Own modules
import KoalaBot
from koala.utils.KoalaDBManager import KoalaDBManager
from koala.cogs.intro_cog import db as intro_db

# Constants
fake_guild_id = 1000
non_existent_guild_id = 9999

# Variables
DBManager = KoalaDBManager(KoalaBot.DATABASE_PATH, KoalaBot.DB_KEY)
DBManager.create_base_tables()


async def add_fake_guild_to_db(id=-1):
    if id == 9999:
        return -1
    if id == -1:
        id = dpyfactory.make_id()
    intro_db.remove_guild_welcome_message(id)
    DBManager.db_execute_commit(
        f"INSERT INTO GuildWelcomeMessages (guild_id, welcome_message) VALUES ({id}, 'fake guild welcome message');")
    return id
