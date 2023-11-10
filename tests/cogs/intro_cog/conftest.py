#!/usr/bin/env python
"""
Testing KoalaBot IntroCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

# Libs
import discord.ext.test as dpytest
import pytest_asyncio
# Own modules
from discord.ext import commands

from koala.cogs import IntroCog
from tests.log import logger
from tests.tests_utils.last_ctx_cog import LastCtxCog


@pytest_asyncio.fixture(autouse=True)
async def utils_cog(bot: commands.Bot):
    utils_cog = LastCtxCog(bot)
    await bot.add_cog(utils_cog)
    dpytest.configure(bot)
    logger.info("Tests starting")
    return utils_cog


@pytest_asyncio.fixture(autouse=True)
async def intro_cog(bot: commands.Bot):
    intro_cog = IntroCog(bot)
    await bot.add_cog(intro_cog)
    dpytest.configure(bot)
    logger.info("Tests starting")
    return intro_cog
