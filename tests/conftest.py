"""
A configuration file for methods useful in all testing with pytest
"""
# Futures

# Built-in/Generic Imports
import os
import sys
import shutil
import time

# Libs
from dotenv import load_dotenv
import pytest
import discord
import discord.ext.commands as commands
import discord.ext.test as dpytest
from pathlib import Path

# Own modules

# Constants


@pytest.fixture(scope='session', autouse=True)
def teardown_config():

    # yield, to let all tests within the scope run
    yield

    # tear_down: then clear table at the end of the scope
    print("Tearing down session")

    from koala.utils.KoalaUtils import get_arg_config_path

    shutil.rmtree(get_arg_config_path(), ignore_errors=True)


@pytest.fixture
async def bot(event_loop):
    import KoalaBot
    intents = discord.Intents.default()
    intents.members = True
    intents.guilds = True
    intents.messages = True
    b = commands.Bot(KoalaBot.COMMAND_PREFIX, loop=event_loop, intents=intents)
    await dpytest.empty_queue()
    dpytest.configure(b)
    return b


@pytest.fixture(autouse=True)
def setup_is_dpytest():
    import KoalaBot
    KoalaBot.is_dpytest = True
    yield
    KoalaBot.is_dpytest = False

