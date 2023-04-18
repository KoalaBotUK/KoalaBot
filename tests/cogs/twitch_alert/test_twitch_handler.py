import pytest
import pytest_asyncio

from koala.cogs.twitch_alert.env import TWITCH_KEY, TWITCH_SECRET
from koala.cogs.twitch_alert.twitch_handler import TwitchAPIHandler


@pytest_asyncio.fixture
async def twitch_api_handler():
    twitch_api_handler = TwitchAPIHandler()
    await twitch_api_handler.setup(TWITCH_KEY, TWITCH_SECRET)
    return twitch_api_handler


@pytest.mark.asyncio
async def test_get_streams_data(twitch_api_handler):
    usernames = ['monstercat', 'jaydwee']
    streams_data = await twitch_api_handler.get_streams_data(usernames)
    assert streams_data is not None


@pytest.mark.asyncio
async def test_get_user_data(twitch_api_handler):
    assert await twitch_api_handler.get_user_data('monstercat') is not None


@pytest.mark.asyncio
async def test_get_game_data(twitch_api_handler):
    assert 'music' in (await twitch_api_handler.get_game_data('26936')).name.lower()


@pytest.mark.asyncio
async def test_get_team_users(twitch_api_handler):
    # assumes uosvge is in the team called uosvge
    members = await twitch_api_handler.get_team_users('uosvge')
    for member in members:
        if member.user_login == 'uosvge':
            assert True
            return
    assert False
