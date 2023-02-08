#!/usr/bin/env python

"""
Testing KoalaBot ReactForRole Cog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import discord.ext.test as dpytest
import pytest
from discord.ext import commands
from sqlalchemy import delete

# Own modules
import koalabot
from koala.cogs import ReactForRole
from koala.cogs.react_for_role.models import GuildRFRRequiredRoles, GuildRFRMessages, RFRMessageEmojiRoles
from koala.db import session_manager
from tests.tests_utils.last_ctx_cog import LastCtxCog

from tests.log import logger

# Constants

# Variables


@pytest.fixture(autouse=True)
async def utils_cog(bot: commands.Bot):
    utils_cog = LastCtxCog(bot)
    await bot.add_cog(utils_cog)
    dpytest.configure(bot)
    logger.info("Tests starting")
    return utils_cog


@pytest.fixture(autouse=True)
async def rfr_cog(bot: commands.Bot):
    rfr_cog = ReactForRole(bot)
    await bot.add_cog(rfr_cog)
    dpytest.configure(bot)
    logger.info("Tests starting")
    return rfr_cog


@pytest.fixture(scope='function', autouse=True)
async def setup_clean_db():
    with session_manager() as session:
        session.execute(delete(GuildRFRMessages))
        session.execute(delete(RFRMessageEmojiRoles))
        session.execute(delete(GuildRFRRequiredRoles))
        session.commit()
