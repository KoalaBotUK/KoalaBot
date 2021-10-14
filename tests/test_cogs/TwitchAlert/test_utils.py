# Futures

# Built-in/Generic Imports
import os
import asyncio

# Libs
import discord.ext.test as dpytest
import mock
import pytest_ordering as pytest
import pytest
import discord
from discord.ext import commands

# Own modules
import KoalaBot
from cogs.TwitchAlert import utils as TwitchAlert
from utils import KoalaDBManager
from utils.KoalaColours import *

# Constants
DB_PATH = "Koala.db"


# Variables




def test_create_live_embed():
    # Create the expected embed with information required
    expected = discord.Embed(colour=KOALA_GREEN, title="https://twitch.tv/test")
    expected.set_author(name="Test is now streaming!", icon_url=TwitchAlert.TWITCH_ICON)
    expected.add_field(name="Stream Title", value="Test Title")
    expected.add_field(name="Playing", value="TestGame")
    expected.set_thumbnail(url="http://koalabot.uk")

    # Create JSON required to pass to method
    stream_info = {'user_name': "Test", 'user_login': "test", 'title': "Test Title"}
    user_info = {'profile_image_url': "http://koalabot.uk"}
    game_info = {'name': "TestGame"}

    # Get response and assert equal
    result = TwitchAlert.create_live_embed(stream_info, user_info, game_info, "")
    assert dpytest.embed_eq(result, expected)

def test_create_live_embed_with_message():
    # Create the expected embed with information required
    expected = discord.Embed(colour=KOALA_GREEN, title="https://twitch.tv/test", description="Hello Message")
    expected.set_author(name="Test is now streaming!", icon_url=TwitchAlert.TWITCH_ICON)
    expected.add_field(name="Stream Title", value="Test Title")
    expected.add_field(name="Playing", value="TestGame")
    expected.set_thumbnail(url="http://koalabot.uk")

    # Create JSON required to pass to method
    stream_info = {'user_name': "Test", 'user_login': "test", 'title': "Test Title"}
    user_info = {'profile_image_url': "http://koalabot.uk"}
    game_info = {'name': "TestGame"}

    # Get response and assert equal
    result = TwitchAlert.create_live_embed(stream_info, user_info, game_info, "Hello Message")
    assert dpytest.embed_eq(result, expected)


def test_split_to_100s_small():
    assert len(TwitchAlert.split_to_100s(list(range(1,99)))) == 1


def test_split_to_100s_medium():
    assert len(TwitchAlert.split_to_100s(list(range(1,150)))) == 2


def test_split_to_100s_large():
    result = TwitchAlert.split_to_100s(list(range(1, 1501)))
    assert len(result) == 16
    for res in result:
        assert len(res) <= 100
