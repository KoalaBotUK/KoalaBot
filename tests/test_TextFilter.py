#!/usr/bin/env python
"""
Testing KoalaBot TextFilter
"""

import asyncio

# Libs
import discord
import discord.ext.test as dpytest
import mock
import pytest
from discord.ext import commands
import time

# Own modules
import KoalaBot
from cogs import BaseCog
from cogs import TextFilter
from tests.utils import TestUtilsCog
from tests.utils.TestUtils import assert_activity
from utils import KoalaDBManager
from utils.KoalaColours import *

# Variables
base_cog = None
tf_cog = None
utils_cog =  None


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global base_cog, tf_cog, utils_cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    base_cog = BaseCog.BaseCog(bot)
    tf_cog = TextFilter.TextFilter(bot)
    tf_cog.tf_database_manager.create_tables()
    utils_cog = TestUtilsCog.TestUtilsCog(bot)
    bot.add_cog(base_cog)
    bot.add_cog(tf_cog)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    print("Tests starting")
    return dpytest.get_config()


def assertBannedWarning(word):
    dpytest.verify_message("Watch your language! Your message: '*" + word + "*' in " + dpytest.get_config().guilds[0].channels[0].mention + " has been deleted by KoalaBot.")


def assertRiskyWarning(word):
    dpytest.verify_message("Watch your language! Your message: '*" + word + "*' in " + dpytest.get_config().guilds[0].channels[0].mention + " contains a 'risky' word. This is a warning.")


def assertEmailWarning(word):
    dpytest.verify_message("Be careful! Your message: '*"+word+"*' in "+dpytest.get_config().guilds[0].channels[0].mention+" includes personal information and has been deleted by KoalaBot.")


def assertFilteredConfirmation(word, type):
    dpytest.verify_message("*"+word+"* has been filtered as **"+type+"**.")


def assertNewIgnore(id):
    dpytest.verify_message("New ignore added: "+id)


def assertRemoveIgnore(id):
    dpytest.verify_message("Ignore removed: "+id)

def createNewModChannelEmbed(channel):
    embed = discord.Embed()
    embed.title = "Koala Moderation - Mod Channel Added"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    embed.add_field(name="Channel Name", value=channel.mention)
    embed.add_field(name="Channel IDs", value=str(channel.id))
    return embed

def listModChannelEmbed(channels):
    embed = discord.Embed()
    embed.title = "Koala Moderation - Mod Channels"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    for channel in channels:
        embed.add_field(name="Name & Channel ID", value=channel.mention + " " + str(channel.id))
    return embed

def listIgnoredEmbed(ignored):
    embed = discord.Embed()
    embed.title = "Koala Moderation - Ignored Users/Channels"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    for ig in ignored:
        embed.add_field(name="Name & ID", value=ig.mention + " " + str(ig.id))
    return embed

def removeModChannelEmbed(channel):
    embed = discord.Embed()
    embed.title = "Koala Moderation - Mod Channel Removed"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    embed.add_field(name="Channel Name", value=channel.mention)
    embed.add_field(name="Channel ID", value=str(channel.id))
    return embed

def createFilteredString(text):
    createTextString = ""
    for current in text:
        createTextString+=current+"\n"
    return createTextString

def filteredWordsEmbed(words,filter,regex):
    wordString = createFilteredString(words)
    filterString = createFilteredString(filter)
    regexString = createFilteredString(regex)
    embed = discord.Embed()
    embed.title = "Koala Moderation - Filtered Words"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    embed.add_field(name="Banned Words", value=wordString)
    embed.add_field(name="Filter Type", value=filterString)
    embed.add_field(name="Is Regex", value=regexString)
    return embed

def cleanup(guildId):
     tf_cog.tf_database_manager.database_manager.db_execute_commit(f"DELETE FROM TextFilter WHERE guild_id=(\"{guildId}\");")

@pytest.mark.asyncio()
async def test_filter_new_word_correct_database():
    old = len(tf_cog.tf_database_manager.database_manager.db_execute_select(f"SELECT filtered_text FROM TextFilter WHERE filtered_text = 'no';"))
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word no", channel=dpytest.get_config().guilds[0].channels[0])
    assertFilteredConfirmation("no","banned")
    assert len(tf_cog.tf_database_manager.database_manager.db_execute_select(f"SELECT filtered_text FROM TextFilter WHERE filtered_text = 'no';")) == old + 1
    cleanup(dpytest.get_config().guilds[0].id)

@pytest.mark.asyncio()
async def test_filter_empty_word():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word")

@pytest.mark.asyncio()
async def test_filter_too_many_arguments():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word a b c d e f g")

@pytest.mark.asyncio()
async def test_filter_risky_word():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word yup risky")
    assertFilteredConfirmation("yup","risky")

    await dpytest.message("yup test")
    assertRiskyWarning("yup test")

    cleanup(dpytest.get_config().guilds[0].id)

@pytest.mark.asyncio()
async def test_unrecognised_filter_type():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word testy unknown")

@pytest.mark.asyncio()
async def test_filter_email_regex():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_regex [a-z0-9]+[\._]?[a-z0-9]+[@]+[herts]+[.ac.uk]")
    assertFilteredConfirmation("[a-z0-9]+[\._]?[a-z0-9]+[@]+[herts]+[.ac.uk]","banned")
    cleanup(dpytest.get_config().guilds[0].id)

@pytest.mark.asyncio()
async def test_filter_various_emails_with_regex():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_regex [a-z0-9]+[\._]?[a-z0-9]+[@]+[herts]+[.ac.uk]")
    assertFilteredConfirmation("[a-z0-9]+[\._]?[a-z0-9]+[@]+[herts]+[.ac.uk]","banned")

    # Should delete and warn
    await dpytest.message("hey stefan@herts.ac.uk")
    assertBannedWarning("hey stefan@herts.ac.uk")

    # Should delete and warn
    await dpytest.message("hey stefan.c.27.abc@herts.ac.uk")
    assertBannedWarning("hey stefan.c.27.abc@herts.ac.uk")

    # Should not warn
    await dpytest.message("hey herts.ac.uk")

    # Should not warn
    await dpytest.message("hey stefan@herts")
    cleanup(dpytest.get_config().guilds[0].id)

@pytest.mark.asyncio()
async def test_unfilter_word_correct_database():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word unfilterboi")
    assertFilteredConfirmation("unfilterboi","banned")
    
    old = len(tf_cog.tf_database_manager.database_manager.db_execute_select(f"SELECT filtered_text FROM TextFilter WHERE filtered_text = 'unfilterboi';"))
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "unfilter_word unfilterboi")
    
    assert len(tf_cog.tf_database_manager.database_manager.db_execute_select(f"SELECT filtered_text FROM TextFilter WHERE filtered_text = 'unfilterboi';")) == old - 1  
    dpytest.verify_message("*unfilterboi* has been unfiltered.")
    cleanup(dpytest.get_config().guilds[0].id)

@pytest.mark.asyncio()
async def test_unfilter_empty():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "unfilter_word")

@pytest.mark.asyncio()
async def test_unfilter_too_many_arguments():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "unfilter_word a b c d e")

@pytest.mark.asyncio()
async def test_list_filtered_words():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word listing1")
    assertFilteredConfirmation("listing1","banned")
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word listing2 risky")
    assertFilteredConfirmation("listing2","risky")

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "check_filtered_words")
    assert_embed = filteredWordsEmbed(['listing1','listing2'],['banned','risky'], ['0','0'])
    dpytest.verify_embed(embed=assert_embed)
    cleanup(dpytest.get_config().guilds[0].id)

@pytest.mark.asyncio()
async def test_list_filtered_words_empty():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "check_filtered_words")
    assert_embed = filteredWordsEmbed([],[],[])
    dpytest.verify_embed(embed=assert_embed)
    cleanup(dpytest.get_config().guilds[0].id)

@pytest.mark.asyncio()
async def test_add_mod_channel():
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=dpytest.get_config().guilds[0])
    dpytest.get_config().channels.append(channel)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "setupModChannel "+str(channel.id))
    assert_embed = createNewModChannelEmbed(channel)
    dpytest.verify_embed(embed=assert_embed)
    cleanup(dpytest.get_config().guilds[0].id)

@pytest.mark.asyncio()
async def test_add_mod_channel_empty():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "setupModChannel")

@pytest.mark.asyncio()
async def test_add_mod_channel_unrecognised_channel():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "setupModChannel 123")

@pytest.mark.asyncio()
async def test_add_mod_channel_too_many_arguments():
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=dpytest.get_config().guilds[0])
    dpytest.get_config().channels.append(channel)
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "setupModChannel "+str(channel.id)+" a b c d e")

@pytest.mark.asyncio()
async def test_remove_mod_channel():
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=dpytest.get_config().guilds[0])
    channelId = str(channel.id)
    dpytest.get_config().channels.append(channel)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "setupModChannel "+channelId)
    assert_embed = createNewModChannelEmbed(channel)
    dpytest.verify_embed(embed=assert_embed)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "removeModChannel "+channelId)
    assert_embed = removeModChannelEmbed(channel)
    dpytest.verify_embed(embed=assert_embed)
    cleanup(dpytest.get_config().guilds[0].id)

@pytest.mark.asyncio()
async def test_remove_mod_channel_empty():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "removeModChannel")

@pytest.mark.asyncio()
async def test_remove_mod_channel_too_many_arguments():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "removeModChannel 123 a b c d e")

@pytest.mark.asyncio()
async def test_remove_mod_channel_unrecognised_channel():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "removeModChannel 123 a b c d e")

@pytest.mark.asyncio()
async def test_list_channels():
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=dpytest.get_config().guilds[0])
    dpytest.get_config().channels.append(channel)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "setupModChannel "+str(channel.id))
    assert_embed = createNewModChannelEmbed(channel)
    dpytest.verify_embed(embed=assert_embed)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "listModChannels")
    assert_embed = listModChannelEmbed([channel])
    dpytest.verify_embed(embed=assert_embed)
    cleanup(dpytest.get_config().guilds[0].id)

@pytest.mark.asyncio()
async def test_list_multiple_channels():
    channel1 = dpytest.backend.make_text_channel(name="TestChannel1", guild=dpytest.get_config().guilds[0])
    channel2 = dpytest.backend.make_text_channel(name="TestChannel2", guild=dpytest.get_config().guilds[0])
    dpytest.get_config().channels.append(channel1)
    dpytest.get_config().channels.append(channel2)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "setupModChannel "+str(channel1.id))
    assert_embed = createNewModChannelEmbed(channel1)
    dpytest.verify_embed(embed=assert_embed)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "setupModChannel "+str(channel2.id))
    assert_embed = createNewModChannelEmbed(channel2)
    dpytest.verify_embed(embed=assert_embed)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "listModChannels")
    assert_embed = listModChannelEmbed([channel1,channel2])
    dpytest.verify_embed(embed=assert_embed)
    cleanup(dpytest.get_config().guilds[0].id)

@pytest.mark.asyncio()
async def test_ignore_channel():
    channel1 = dpytest.backend.make_text_channel(name="TestChannel1", guild=dpytest.get_config().guilds[0])

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word ignoreme")
    assertFilteredConfirmation("ignoreme","banned")

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "ignoreChannel " + channel1.mention)
    assertNewIgnore(channel1.mention)

    # Should be ignored
    await dpytest.message("ignoreme", channel=channel1)

    # Should be deleted and warned
    await dpytest.message("ignoreme")
    assertBannedWarning("ignoreme")

    cleanup(dpytest.get_config().guilds[0].id)

@pytest.mark.asyncio()
async def test_ignore_user():
    message = await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word ignoreuser")
    assertFilteredConfirmation("ignoreuser","banned")

    # Should be deleted and warned
    await dpytest.message("ignoreuser")
    assertBannedWarning("ignoreuser")

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "ignoreUser " + message.author.mention)
    assertNewIgnore(message.author.mention)

    # Should be ignored
    await dpytest.message("ignoreuser")
    cleanup(dpytest.get_config().guilds[0].id)

@pytest.mark.asyncio()
async def test_ignore_empty_user():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "ignoreUser")

@pytest.mark.asyncio()
async def test_unignore_channel():
    message = await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word ignoreuser")
    assertFilteredConfirmation("ignoreuser","banned")

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "ignoreChannel " + dpytest.get_config().guilds[0].channels[0].mention)
    assertNewIgnore(dpytest.get_config().guilds[0].channels[0].mention)

    # Should be ignored
    await dpytest.message("ignoreuser")

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "unignore " + dpytest.get_config().guilds[0].channels[0].mention)
    assertRemoveIgnore(dpytest.get_config().guilds[0].channels[0].mention)

    # Should be deleted and warned
    await dpytest.message("ignoreuser")
    assertBannedWarning("ignoreuser")

@pytest.mark.asyncio()
async def test_list_ignored():
    mes = await dpytest.message(KoalaBot.COMMAND_PREFIX + "ignoreChannel " + dpytest.get_config().guilds[0].channels[0].mention)
    assertNewIgnore(dpytest.get_config().guilds[0].channels[0].mention)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "ignoreUser " + mes.author.mention)
    assertNewIgnore(mes.author.mention)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "listIgnored")
    assert listIgnoredEmbed([dpytest.get_config().guilds[0].channels[0], mes.author])

@pytest.fixture(autouse=True)
async def clear_queue():
    await dpytest.empty_queue()
    yield dpytest

@pytest.fixture(scope='session', autouse=True)
def setup_is_dpytest():
    KoalaBot.is_dpytest = True
    yield
    KoalaBot.is_dpytest = False
