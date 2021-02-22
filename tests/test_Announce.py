import random
from typing import *

# Libs
import discord
import discord.ext.test as dpytest
import mock
import pytest
from discord.ext import commands
from discord.ext.test import factories as dpyfactory

# Own modules
import KoalaBot
from cogs import Announce
from cogs.Announce import AnnounceDBManager
from tests.utils import TestUtils as utils
from tests.utils import TestUtilsCog
from utils.KoalaDBManager import KoalaDBManager

# Varibales
announce_cog: Announce.Announce = None
utils_cog: TestUtilsCog.TestUtilsCog = None
DBManager = AnnounceDBManager(KoalaBot.database_manager)
DBManager.create_tables()


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global announce_cog
    global utils_cog
    bot: commands.Bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    announce_cog = Announce.Announce(bot)
    utils_cog = TestUtilsCog.TestUtilsCog(bot)
    bot.add_cog(announce_cog)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    print("Tests starting")


@pytest.mark.asyncio
async def test_is_allowed_to_create_true():
    """
    config = dpytest.get_config()
    guild = config.guilds[0]
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "announce create")
    dpytest.verify_message()
    assert not ColourRole.is_allowed_to_change_colour(ctx)"""
    assert False, "Not Implemented"
