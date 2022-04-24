#!/usr/bin/env python

"""
Testing utilities for KoalaBot tests

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import random
from string import ascii_letters

# Libs
import discord
import emoji
from discord.ext.test import factories as dpyfactory

# Own modules

# Constants
unicode_emojis = list(dict(emoji.UNICODE_EMOJI.get('en')).values())
emoji_unicodes = list(dict(emoji.EMOJI_UNICODE.get('en')).values())


# Variables


def assert_activity(activity: discord.Activity, application_id=None, name=None, url=None,
                    type=None, state=None, details=None, emoji=None, start=None, end=None,
                    large_image_url=None, small_image_url=None, large_image_text=None, small_image_text=None):
    """
    A method that asserts all activity properties of the given activity are as provided

    :param activity: The outcome to be tested against
    :param application_id: assert the application ID of the activity is the same as this
    :param name: assert the name of the activity is the same as this
    :param url: assert the url of the activity is the same as this
    :param type: assert the type of the activity is the same as this
    :param state: assert the state of the activity is the same as this
    :param details: assert the details of the activity is the same as this
    :param emoji: assert the emoji of the activity is the same as this
    :param start: assert the start of the activity is the same as this
    :param end: assert the end of the activity is the same as this
    :param large_image_url: assert the large_image_url of the activity is the same as this
    :param small_image_url: assert the small_image_url of the activity is the same as this
    :param large_image_text: assert the large_image_text of the activity is the same as this
    :param small_image_text: assert the small_image_text of the activity is the same as this
    """
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


def fake_guild_emoji(guild: discord.Guild) -> discord.Emoji:
    fake_emoji = discord.Emoji(guild=guild, state=None,
                               data={'require_colons': True, 'managed': False, 'animated': False,
                                     'name': fake_custom_emoji_name_str(), 'id': fake_id_str(), 'available': True})
    return fake_emoji

def fake_partial_emoji() -> discord.PartialEmoji:
    if random.choice([True, False]):
        fake_emoji = discord.PartialEmoji(name=fake_custom_emoji_name_str(), animated=random.choice([True, False]), id=dpyfactory.make_id)
    else:
        fake_emoji = discord.PartialEmoji(name=fake_unicode_emoji())
    return fake_emoji


def fake_guild_role(guild: discord.Guild) -> discord.Role:
    fake_role = discord.Role(guild=guild, state=None,
                             data={'id': dpyfactory.make_id(), 'name': fake_custom_emoji_name_str(),
                                   'mentionable': True, 'hoist': True, 'managed': False,
                                   'colour': random.randint(0, 16777215), 'permissions': 8})
    guild._add_role(fake_role)
    return fake_role


def fake_custom_emoji_str_rep() -> str:
    """
    Creates a fake string representation of a discord custom emoji.
    :return:
    """
    emoji_str = ""
    emoji_str += random.choice(["<a:", "<:"])
    emoji_str += ''.join(random.choice(ascii_letters) for i in range(random.randint(4, 12)))
    emoji_str += f":{dpyfactory.make_id()}>"
    return emoji_str


def fake_custom_emoji_name_str() -> str:
    return ''.join(random.choice(ascii_letters) for i in range(random.randint(4, 12)))


def fake_unicode_emoji() -> str:
    """
    Creates a fake unicode emoji (the string representation with colons)
    :return:
    """
    return random.choice(unicode_emojis)

def fake_emoji_unicode() -> str:
    """
    Returns a random unicode emoji's unicode codepoint
    """
    return random.choice(emoji_unicodes)

def fake_role_mention() -> str:
    """
    Creates a fake role mention string.
    :return:
    """
    return "<@&" + str(dpyfactory.make_id()) + ">"


def fake_id_str() -> str:
    """
    Creates a fake id string, e.g. message ID, role ID, etc.
    :return:
    """
    return str(dpyfactory.make_id())


class FakeAuthor:
    """
    A class that acts as a discord.Member to replace the ctx.author on a context (ctx)
    """

    def __init__(self, name="FakeUser#0001", id=-1, all_permissions=False):
        """
        Initialises class variables and creates a random id if not specified
        :param name: the name of the user including identifier (e.g. KoalaBotUK#1075)
        :param id: The discord ID of the user
        :param all_permissions: If the user should be given all permissions (admin etc) or none
        :param roles: The role IDs of the user's roles
        """
        self.name = name
        if id == -1:
            self.id = dpyfactory.make_id()
        else:
            self.id = id
        self.allPermissions = all_permissions

    def __str__(self):
        """
        The string of this class is the name
        :return: name
        """
        return self.name

    @property
    def guild_permissions(self):
        """
        Imitates discord.Member.guild_permissions and redirects according to allPermissions
        :return: discord permissions (all or none)
        """
        if self.allPermissions:
            return discord.Permissions.all()
        else:
            return discord.Permissions.none()
