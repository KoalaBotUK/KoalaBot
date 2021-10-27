from koala.cogs.TwitchAlert.twitch_handler import TwitchAPIHandler
from koala.cogs.TwitchAlert.utils import TWITCH_KEY, TWITCH_SECRET
import pytest

@pytest.fixture
def twitch_api_handler():
    return TwitchAPIHandler(TWITCH_KEY, TWITCH_SECRET)


@pytest.mark.asyncio
async def test_get_streams_data(twitch_api_handler):
    usernames = ['monstercat', 'jaydwee']
    streams_data = twitch_api_handler.get_streams_data(usernames)
    assert streams_data is not None


@pytest.mark.asyncio
async def test_get_user_data(twitch_api_handler):
    assert twitch_api_handler.get_user_data('monstercat') is not None


@pytest.mark.asyncio
async def test_get_game_data(twitch_api_handler):
    assert 'music' in (twitch_api_handler.get_game_data('26936')).get('name').lower()


@pytest.mark.asyncio
async def test_get_team_users(twitch_api_handler):
    # assumes uosvge is in the team called uosvge
    members = twitch_api_handler.get_team_users('uosvge')
    for member in members:
        if member.get('user_login') == 'uosvge':
            assert True
            return
    assert False
