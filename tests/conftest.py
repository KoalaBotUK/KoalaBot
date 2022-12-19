"""
A configuration file for methods useful in all testing with pytest
"""
# Futures

# Built-in/Generic Imports
import shutil

# Libs
import pytest
import discord
import discord.ext.commands as commands
import discord.ext.test as dpytest
import pytest_asyncio

# Own modules
import koalabot
from koala.db import session_manager
from tests.log import logger
# Constants

pytest_plugins = 'aiohttp.pytest_plugin'


@pytest.fixture(scope='session', autouse=True)
def teardown_config():

    # yield, to let all tests within the scope run
    yield

    # tear_down: then clear table at the end of the scope
    logger.info("Tearing down session")

    from koala.utils import get_arg_config_path

    shutil.rmtree(get_arg_config_path(), ignore_errors=True)


@pytest_asyncio.fixture
async def bot():
    import koalabot
    intents = discord.Intents.default()
    intents.members = True
    intents.guilds = True
    intents.messages = True
    intents.message_content = True
    b = commands.Bot(koalabot.COMMAND_PREFIX, intents=intents)
    await b._async_setup_hook()
    await dpytest.empty_queue()
    dpytest.configure(b)
    return b


@pytest.fixture(autouse=True)
def setup_is_dpytest():
    koalabot.is_dpytest = True
    yield
    koalabot.is_dpytest = False


@pytest_asyncio.fixture
async def session():
    with session_manager() as session:
        yield session
