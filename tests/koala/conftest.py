"""
A configuration file for methods useful in all testing with pytest
"""
# Futures

# Built-in/Generic Imports

import discord
import discord.ext.test as dpytest
# Libs
import pytest
import pytest_asyncio

import koala.db as db
# Own modules
import koalabot

# Constants


@pytest_asyncio.fixture
async def bot():
    import koalabot
    intents = discord.Intents.default()
    intents.members = True
    intents.guilds = True
    intents.messages = True
    intents.message_content = True
    b = koalabot.KoalaBot(koalabot.COMMAND_PREFIX, intents=intents)
    await b._async_setup_hook()
    await dpytest.empty_queue()
    dpytest.configure(b)
    return b


@pytest.fixture(autouse=True)
def setup_is_dpytest():
    db.__create_sqlite_tables()
    koalabot.is_dpytest = True
    yield
    koalabot.is_dpytest = False
