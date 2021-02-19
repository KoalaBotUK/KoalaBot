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
from cogs import ReactForRole
from cogs.ReactForRole import ReactForRoleDBManager
from tests.utils import TestUtils as utils
from tests.utils import TestUtilsCog
from utils.KoalaDBManager import KoalaDBManager

def setup_function():
    """ setup any state specific to the execution of the given module."""
    global announce_cog
    global utils_cog
    bot: commands.Bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    announce_cog = ReactForRole.ReactForRole(bot)
    utils_cog = TestUtilsCog.TestUtilsCog(bot)
    bot.add_cog(announce_cog)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    print("Tests starting")