#!/usr/bin/env python

"""
Koala Bot Base Code

Commented using reStructuredText (reST)
"""
__author__ = "Jack Draper, Kieran Allinson, Viraj Shah"
__copyright__ = "Copyright (c) 2020 KoalaBot"
__credits__ = ["Jack Draper", "Kieran Allinson", "Viraj Shah"]
__license__ = "MIT License"
__version__ = "0.0.1"
__maintainer__ = "Jack Draper, Kieran Allinson, Viraj Shah"
__email__ = "koalabotuk@gmail.com"
__status__ = "Development"  # "Prototype", "Development", or "Production"

# Futures

# Built-in/Generic Imports
import os

# Libs
import discord
from discord.ext.test import factories as dpyfact
from dotenv import load_dotenv


# Own modules
import KoalaBot


# Constants
load_dotenv()
BOT_NAME = os.environ['DISCORD_NAME']
BOT_TEST_TOKEN = os.environ['DISCORD_TEST_TOKEN']
BOT_TOKEN = os.environ['DISCORD_TOKEN']

# Variables


def assert_activity(activity: discord.Activity, application_id=None, name=None, url=None,
                    type=None, state=None, details=None, emoji=None, start=None, end=None,
                    large_image_url=None, small_image_url=None, large_image_text=None, small_image_text=None):
    # TODO: Add timestamps, assets, party
    assert activity.application_id == application_id \
           and activity.name == name \
           and activity.url == url \
           and activity.type == type \
           and activity.state == state \
           and activity.details == details \
           and activity.emoji == emoji \
           and activity.start == start \
           and activity.end == end \
           and activity.large_image_url == large_image_url \
           and activity.small_image_url == small_image_url \
           and activity.large_image_text == large_image_text \
           and activity.small_image_text == small_image_text

"""
def run_bot(koala):
       koala.client.run(BOT_TOKEN)


def run_test_bot(distest, test_collector):
       distest.run_command_line_bot(BOT_NAME, BOT_TEST_TOKEN, "all", 729700330840915978, True, test_collector, 5)
"""


class FakeAuthor:
    def __init__(self, name="FakeUser#0001", id=-1, allPermissions=False):
        self.name = name
        if id == -1:
            self.id = dpyfact.make_id()
        else:
            self.id = id
        self.allPermissions = allPermissions

    def __str__(self):
        return self.name

    @property
    def guild_permissions(self):
        if self.allPermissions:
            return discord.Permissions.all()
        else:
            return discord.Permissions.none()
