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
import koalabot
from koala.db import session_manager
from koala.cogs.intro_cog import db as intro_db
from koala.cogs.intro_cog.models import GuildWelcomeMessages

# Constants
fake_guild_id = 1000
non_existent_guild_id = 9999

# Variables


async def add_fake_guild_to_db(id=-1):
    with session_manager() as session:
        if id == 9999:
            return -1
        if id == -1:
            id = dpyfactory.make_id()
        intro_db.remove_guild_welcome_message(id)
        session.add(GuildWelcomeMessages(guild_id=id, welcome_message='fake guild welcome message'))
        session.commit()
        return id
