#!/usr/bin/env python
"""
Testing KoalaBot TextFilter

Commented using reStructuredText (reST)
"""

import asyncio

# Libs
import discord
import discord.ext.test as dpytest
import mock
import pytest
from discord.ext import commands

# Own modules
import KoalaBot
from cogs import BaseCog
from cogs import TextFilter
from tests.utils import TestUtilsCog
from tests.utils.TestUtils import assert_activity
from utils import KoalaDBManager

# Constants

# Variables
base_cog = None
tf_cog = None
utils_cog =  None


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global base_cog, tf_cog, utils_cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    base_cog = BaseCog.BaseCog(bot)
    tf_cog = TextFilter.TextFilterCog(bot)
    tf_cog.tf_database_manager.create_tables()
    utils_cog = TestUtilsCog.TestUtilsCog(bot)
    bot.add_cog(base_cog)
    bot.add_cog(tf_cog)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    print("Tests starting")

@pytest.mark.asyncio()
async def test_filter_new_word_correct_text():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_Word no")
    dpytest.verify_message("*no* has been filtered.")
    dpytest.verify_message("Watch your language! Your message: '*k!filter_Word no*' in #Channel_0 has been deleted by KoalaBot.")
    
@pytest.mark.asyncio()
async def test_unfilter_word_correct_text():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_Word unfilterboi")
    dpytest.verify_message("*unfilterboi* has been filtered.")
    dpytest.verify_message("Watch your language! Your message: '*k!filter_Word unfilterboi*' in #Channel_0 has been deleted by KoalaBot.")
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "unfilter_Word unfilterboi")
    dpytest.verify_message("*unfilterboi* has been unfiltered.")

@pytest.mark.asyncio()
async def test_filter_new_word_correct_database():
    old = len(tf_cog.tf_database_manager.database_manager.db_execute_select("SELECT filtered_text FROM TextFilter WHERE filtered_text = 'no'"))
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_Word no")
    assert len(tf_cog.tf_database_manager.database_manager.db_execute_select("SELECT filtered_text FROM TextFilter WHERE filtered_text = 'no'")) == old + 1 

@pytest.mark.asyncio()
async def test_unfilter_word_correct_database():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_Word unfilterboi")
    old = len(tf_cog.tf_database_manager.database_manager.db_execute_select("SELECT filtered_text FROM TextFilter WHERE filtered_text = 'unfilterboi'"))
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "unfilter_Word unfilterboi")
    assert len(tf_cog.tf_database_manager.database_manager.db_execute_select("SELECT filtered_text FROM TextFilter WHERE filtered_text = 'unfilterboi';")) == old - 1  
