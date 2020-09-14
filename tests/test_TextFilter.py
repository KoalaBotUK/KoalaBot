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
from utils.KoalaColours import *

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
async def test_filter_new_word_correct_database():
    old = len(tf_cog.tf_database_manager.database_manager.db_execute_select("SELECT filtered_text FROM TextFilter WHERE filtered_text = 'no'"))
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word no")
    dpytest.verify_message("*no* has been filtered.")
    dpytest.verify_message("Watch your language! Your message: '*k!filter_word no*' in "+dpytest.get_config().guilds[0].channels[0].mention +" has been deleted by KoalaBot.")
    assert len(tf_cog.tf_database_manager.database_manager.db_execute_select("SELECT filtered_text FROM TextFilter WHERE filtered_text = 'no'")) == old + 1 

@pytest.mark.asyncio()
async def test_unfilter_word_correct_database():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word unfilterboi")
    dpytest.verify_message("*unfilterboi* has been filtered.")
    dpytest.verify_message("Watch your language! Your message: '*k!filter_word unfilterboi*' in "+dpytest.get_config().guilds[0].channels[0].mention +" has been deleted by KoalaBot.")
    
    old = len(tf_cog.tf_database_manager.database_manager.db_execute_select("SELECT filtered_text FROM TextFilter WHERE filtered_text = 'unfilterboi'"))
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "unfilter_word unfilterboi")
    assert len(tf_cog.tf_database_manager.database_manager.db_execute_select("SELECT filtered_text FROM TextFilter WHERE filtered_text = 'unfilterboi';")) == old - 1  
    dpytest.verify_message("*unfilterboi* has been unfiltered.")

@pytest.mark.asyncio()
async def test_list_filtered_words():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word listing1")
    dpytest.verify_message("*listing1* has been filtered.")
    dpytest.verify_message("Watch your language! Your message: '*k!filter_word listing1*' in "+dpytest.get_config().guilds[0].channels[0].mention +" has been deleted by KoalaBot.")
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word listing2")
    dpytest.verify_message("*listing2* has been filtered.")
    dpytest.verify_message("Watch your language! Your message: '*k!filter_word listing2*' in "+dpytest.get_config().guilds[0].channels[0].mention +" has been deleted by KoalaBot.")

    assert_embed = discord.Embed()
    assert_embed.title = "Filtered Words"
    assert_embed.colour = KOALA_GREEN
    assert_embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    assert_embed.add_field(name="Banned Words", value="listing1\nlisting2\n")
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "check_filtered_words")
    dpytest.verify_embed(embed=assert_embed)

