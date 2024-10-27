"""
A configuration file for methods useful in all testing with pytest
"""
# Futures

# Built-in/Generic Imports
import shutil

# Libs
import pytest
import pytest_asyncio

# Own modules
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

    from koala.env import CONFIG_PATH

    shutil.rmtree(CONFIG_PATH, ignore_errors=True)


@pytest_asyncio.fixture
async def session():
    with session_manager() as session:
        yield session
