"""
A configuration file for methods useful in all testing with pytest
"""
# Futures

# Built-in/Generic Imports
import os

# Libs
import pytest
import discord
import discord.ext.commands as commands
import discord.ext.test as dpytest

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


@pytest.fixture(autouse=True)
def setup_is_dpytest():
    KoalaBot.is_dpytest = True
    yield
    KoalaBot.is_dpytest = False


@pytest.fixture(scope="session", autouse=True)
def delete_database():
    print("deleting database")
    os.remove(KoalaBot.DATABASE_PATH)
