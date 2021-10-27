# Futures

# Built-in/Generic Imports

# Libs
import discord.ext.test as dpytest
import discord

# Own modules
from koala.cogs.TwitchAlert import utils
from koala.utils.KoalaColours import KOALA_GREEN

# Constants
DB_PATH = "Koala.db"


# Variables


def test_create_live_embed():
    # Create the expected embed with information required
    expected = discord.Embed(colour=KOALA_GREEN, title="https://twitch.tv/test")
    expected.set_author(name="Test is now streaming!", icon_url=utils.TWITCH_ICON)
    expected.add_field(name="Stream Title", value="Test Title")
    expected.add_field(name="Playing", value="TestGame")
    expected.set_thumbnail(url="http://koalabot.uk")

    # Create JSON required to pass to method
    stream_info = {'user_name': "Test", 'user_login': "test", 'title': "Test Title"}
    user_info = {'profile_image_url': "http://koalabot.uk"}
    game_info = {'name': "TestGame"}

    # Get response and assert equal
    result = utils.create_live_embed(stream_info, user_info, game_info, "")
    assert dpytest.embed_eq(result, expected)


def test_create_live_embed_with_message():
    # Create the expected embed with information required
    expected = discord.Embed(colour=KOALA_GREEN, title="https://twitch.tv/test", description="Hello Message")
    expected.set_author(name="Test is now streaming!", icon_url=utils.TWITCH_ICON)
    expected.add_field(name="Stream Title", value="Test Title")
    expected.add_field(name="Playing", value="TestGame")
    expected.set_thumbnail(url="http://koalabot.uk")

    # Create JSON required to pass to method
    stream_info = {'user_name': "Test", 'user_login': "test", 'title': "Test Title"}
    user_info = {'profile_image_url': "http://koalabot.uk"}
    game_info = {'name': "TestGame"}

    # Get response and assert equal
    result = utils.create_live_embed(stream_info, user_info, game_info, "Hello Message")
    assert dpytest.embed_eq(result, expected)


def test_create_live_embed_without_game():
    # Create the expected embed with information required
    expected = discord.Embed(colour=KOALA_GREEN, title="https://twitch.tv/test", description="Hello Message")
    expected.set_author(name="Test is now streaming!", icon_url=utils.TWITCH_ICON)
    expected.add_field(name="Stream Title", value="Test Title")
    expected.add_field(name="Playing", value="No Category")
    expected.set_thumbnail(url="http://koalabot.uk")

    # Create JSON required to pass to method
    stream_info = {'user_name': "Test", 'user_login': "test", 'title': "Test Title"}
    user_info = {'profile_image_url': "http://koalabot.uk"}

    # Get response and assert equal
    result = utils.create_live_embed(stream_info, user_info, None, "Hello Message")
    assert dpytest.embed_eq(result, expected)


def test_split_to_100s_small():
    assert len(utils.split_to_100s(list(range(1,99)))) == 1


def test_split_to_100s_medium():
    assert len(utils.split_to_100s(list(range(1,150)))) == 2


def test_split_to_100s_large():
    result = utils.split_to_100s(list(range(1, 1501)))
    assert len(result) == 16
    for res in result:
        assert len(res) <= 100


def test_split_to_100s_empty():
    result = utils.split_to_100s([])
    assert result == []
