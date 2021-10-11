"""
A configuration file for methods useful in all testing with pytest
"""
# Futures

# Built-in/Generic Imports

import discord
import discord.ext.commands as commands
import discord.ext.test as dpytest
# Libs
import pytest

# Own modules
import KoalaBot


# Constants

@pytest.fixture
async def bot(event_loop):
    intents = discord.Intents.default()
    intents.members = True
    intents.guilds = True
    intents.messages = True
    b = commands.Bot(KoalaBot.COMMAND_PREFIX, loop=event_loop, intents=intents)
    await dpytest.empty_queue()
    dpytest.configure(b)
    return b


@pytest.fixture(autouse=False)
async def bot_no_configure(event_loop):
    """
    The bot conftest method but with no dpytest.configure() method call
    """
    intents = discord.Intents.default()
    intents.members = True
    intents.guilds = True
    intents.messages = True
    b = commands.Bot(KoalaBot.COMMAND_PREFIX, loop=event_loop, intents=intents)
    await dpytest.empty_queue()
    return b


@pytest.fixture(autouse=True)
def setup_is_dpytest():
    KoalaBot.is_dpytest = True
    yield
    KoalaBot.is_dpytest = False
