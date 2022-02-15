#!/usr/bin/env python
"""
Testing KoalaBot TextFilter
"""

# Libs
import discord
import discord.ext.test as dpytest
import pytest
from sqlalchemy import select, delete

# Own modules
import koalabot
from koala.cogs import BaseCog
from tests.tests_utils import LastCtxCog
from koala.colours import KOALA_GREEN
from koala.utils import is_int
from koala.db import session_manager

from koala.cogs import TextFilter as TextFilterCog
from koala.cogs.text_filter.db import TextFilterDBManager
from koala.cogs.text_filter.models import TextFilter, TextFilterModeration
from tests.log import logger

# Variables


@pytest.fixture(scope="function", autouse=True)
def utils_cog(bot: discord.ext.commands.Bot):
    utils_cog = LastCtxCog.LastCtxCog(bot)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    logger.info("Tests starting")
    return utils_cog


@pytest.fixture(scope="function", autouse=True)
def base_cog(bot: discord.ext.commands.Bot):
    base_cog = BaseCog(bot)
    bot.add_cog(base_cog)
    dpytest.configure(bot)
    logger.info("Tests starting")
    return base_cog


@pytest.fixture(scope="function", autouse=True)
async def tf_cog(bot: discord.ext.commands.Bot):
    tf_cog = TextFilterCog(bot)
    bot.add_cog(tf_cog)
    dpytest.configure(bot)
    logger.info("Tests starting")
    return tf_cog


def assert_banned_warning(word):
    assert dpytest.verify().message().content(
        "Watch your language! Your message: '*" + word + "*' in " + dpytest.get_config().guilds[0].channels[
            0].mention + " has been deleted by KoalaBot.")


def assert_risky_warning(word):
    assert dpytest.verify().message().content(
        "Watch your language! Your message: '*" + word + "*' in " + dpytest.get_config().guilds[0].channels[
            0].mention + " contains a 'risky' word. This is a warning.")


def assert_email_warning(word):
    assert dpytest.verify().message().content(
        "Be careful! Your message: '*" + word + "*' in " + dpytest.get_config().guilds[0].channels[
            0].mention + " includes personal information and has been deleted by KoalaBot.")


def assert_filtered_confirmation(word, type):
    assert dpytest.verify().message().content("*" + word + "* has been filtered as **" + type + "**.")


def assert_new_ignore(id):
    assert dpytest.verify().message().content("New ignore added: " + id)


def assert_remove_ignore(id):
    assert dpytest.verify().message().content("Ignore removed: " + id)


def create_new_mod_channel_embed(channel):
    embed = discord.Embed()
    embed.title = "Koala Moderation - Mod Channel Added"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    embed.add_field(name="Channel Name", value=channel.mention)
    embed.add_field(name="Channel IDs", value=str(channel.id))
    return embed


def list_mod_channel_embed(channels):
    embed = discord.Embed()
    embed.title = "Koala Moderation - Mod Channels"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    for channel in channels:
        embed.add_field(name="Name & Channel ID", value=channel.mention + " " + str(channel.id))
    return embed


def list_ignored_embed(ignored):
    embed = discord.Embed()
    embed.title = "Koala Moderation - Ignored Users/Channels"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    for ig in ignored:
        embed.add_field(name="Name & ID", value=ig.mention + " " + str(ig.id))
    return embed


def remove_mod_channel_embed(channel):
    embed = discord.Embed()
    embed.title = "Koala Moderation - Mod Channel Removed"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    embed.add_field(name="Channel Name", value=channel.mention)
    embed.add_field(name="Channel ID", value=str(channel.id))
    return embed


def create_filtered_string(text):
    create_text_string = ""
    for current in text:
        create_text_string += current + "\n"
    return create_text_string


def filtered_words_embed(words, filter, regex):
    word_string = create_filtered_string(words)
    filter_string = create_filtered_string(filter)
    regex_string = create_filtered_string(regex)
    embed = discord.Embed()
    embed.title = "Koala Moderation - Filtered Words"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    embed.add_field(name="Banned Words", value=word_string)
    embed.add_field(name="Filter Type", value=filter_string)
    embed.add_field(name="Is Regex", value=regex_string)
    return embed


def cleanup(guild_id, tf_cog, session):
    session.execute(delete(TextFilter).filter_by(guild_id=guild_id))


@pytest.mark.asyncio()
async def test_filter_new_word_correct_database(tf_cog):
    with session_manager() as session:
        old = len(session.execute(select(TextFilter.filtered_text).filter_by(filtered_text="no")).all())
        await dpytest.message(koalabot.COMMAND_PREFIX + "filter_word no",
                              channel=dpytest.get_config().guilds[0].channels[0])
        assert_filtered_confirmation("no", "banned")
        assert len(session.execute(select(TextFilter.filtered_text).filter_by(filtered_text="no")).all()) == old + 1
        cleanup(dpytest.get_config().guilds[0].id, tf_cog, session)


@pytest.mark.asyncio()
async def test_filter_empty_word():
    with pytest.raises(Exception):
        await dpytest.message(koalabot.COMMAND_PREFIX + "filter_word")


@pytest.mark.asyncio()
async def test_filter_too_many_arguments():
    with pytest.raises(Exception):
        await dpytest.message(koalabot.COMMAND_PREFIX + "filter_word a b c d e f g")


@pytest.mark.asyncio()
async def test_filter_risky_word(tf_cog):
    with session_manager() as session:
        await dpytest.message(koalabot.COMMAND_PREFIX + "filter_word yup risky")
        assert_filtered_confirmation("yup", "risky")

        await dpytest.message("yup test")
        assert_risky_warning("yup test")

        cleanup(dpytest.get_config().guilds[0].id, tf_cog, session)


@pytest.mark.asyncio()
async def test_unrecognised_filter_type():
    with pytest.raises(Exception):
        await dpytest.message(koalabot.COMMAND_PREFIX + "filter_word testy unknown")


@pytest.mark.asyncio()
async def test_filter_email_regex(tf_cog):
    with session_manager() as session:
        await dpytest.message(koalabot.COMMAND_PREFIX + r"filter_regex [a-z0-9]+[\._]?[a-z0-9]+[@]+[herts]+[.ac.uk]")
        assert_filtered_confirmation(r"[a-z0-9]+[\._]?[a-z0-9]+[@]+[herts]+[.ac.uk]", "banned")
        cleanup(dpytest.get_config().guilds[0].id, tf_cog, session)


@pytest.mark.asyncio()
async def test_invalid_regex(tf_cog):
    with session_manager() as session:
        with pytest.raises(Exception):
            await dpytest.message(koalabot.COMMAND_PREFIX + "filter_regex [")
        cleanup(dpytest.get_config().guilds[0].id, tf_cog, session)


@pytest.mark.asyncio()
async def test_normal_filter_does_not_recognise_regex():
    await dpytest.message(koalabot.COMMAND_PREFIX + "filter \"^verify [a-zA-Z0-9]+@soton.ac.uk$\"")
    assert_filtered_confirmation("^verify [a-zA-Z0-9]+@soton.ac.uk$", "banned")

    await dpytest.message("verify abc@soton.ac.uk")
    assert dpytest.verify().message().nothing()


@pytest.mark.asyncio()
async def test_filter_various_emails_with_regex(tf_cog):
    with session_manager() as session:
        await dpytest.message(koalabot.COMMAND_PREFIX + r"filter_regex [a-z0-9]+[\._]?[a-z0-9]+[@]+[herts]+[.ac.uk]")
        assert_filtered_confirmation(r"[a-z0-9]+[\._]?[a-z0-9]+[@]+[herts]+[.ac.uk]", "banned")

        # Should delete and warn
        await dpytest.message("hey stefan@herts.ac.uk")
        assert_banned_warning("hey stefan@herts.ac.uk")

        # Should delete and warn
        await dpytest.message("hey stefan.c.27.abc@herts.ac.uk")
        assert_banned_warning("hey stefan.c.27.abc@herts.ac.uk")

        # Should not warn
        await dpytest.message("hey herts.ac.uk")
        assert dpytest.verify().message().nothing()

        # Should not warn
        await dpytest.message("hey stefan@herts")
        assert dpytest.verify().message().nothing()

        cleanup(dpytest.get_config().guilds[0].id, tf_cog, session)


@pytest.mark.asyncio()
async def test_unfilter_word_correct_database(tf_cog):
    with session_manager() as session:
        await dpytest.message(koalabot.COMMAND_PREFIX + "filter_word unfilterboi")
        assert_filtered_confirmation("unfilterboi", "banned")

        old = len(session.execute(select(TextFilter.filtered_text).filter_by(filtered_text='unfilterboi')).all())
        await dpytest.message(koalabot.COMMAND_PREFIX + "unfilter_word unfilterboi")

        assert len(session.execute(select(TextFilter.filtered_text)
                                   .filter_by(filtered_text='unfilterboi')).all()) == old - 1
        assert dpytest.verify().message().content("*unfilterboi* has been unfiltered.")
        cleanup(dpytest.get_config().guilds[0].id, tf_cog, session)


@pytest.mark.asyncio()
async def test_unfilter_empty():
    with pytest.raises(Exception):
        await dpytest.message(koalabot.COMMAND_PREFIX + "unfilter_word")


@pytest.mark.asyncio()
async def test_unfilter_too_many_arguments():
    with pytest.raises(Exception):
        await dpytest.message(koalabot.COMMAND_PREFIX + "unfilter_word a b c d e")


@pytest.mark.asyncio()
async def test_list_filtered_words(tf_cog):
    with session_manager() as session:
        await dpytest.message(koalabot.COMMAND_PREFIX + "filter_word listing1")
        assert_filtered_confirmation("listing1", "banned")
        await dpytest.message(koalabot.COMMAND_PREFIX + "filter_word listing2 risky")
        assert_filtered_confirmation("listing2", "risky")

        await dpytest.message(koalabot.COMMAND_PREFIX + "check_filtered_words")
        assert_embed = filtered_words_embed(['listing1', 'listing2'], ['banned', 'risky'], ['0', '0'])
        assert dpytest.verify().message().embed(embed=assert_embed)
        cleanup(dpytest.get_config().guilds[0].id, tf_cog, session)


@pytest.mark.asyncio()
async def test_list_filtered_words_empty(tf_cog):
    with session_manager() as session:
        await dpytest.message(koalabot.COMMAND_PREFIX + "check_filtered_words")
        assert_embed = filtered_words_embed([], [], [])
        assert dpytest.verify().message().embed(embed=assert_embed)
        cleanup(dpytest.get_config().guilds[0].id, tf_cog, session)


@pytest.mark.asyncio()
async def test_add_mod_channel(tf_cog):
    with session_manager() as session:
        channel = dpytest.backend.make_text_channel(name="TestChannel", guild=dpytest.get_config().guilds[0])
        dpytest.get_config().channels.append(channel)

        await dpytest.message(koalabot.COMMAND_PREFIX + "setupModChannel " + str(channel.id))
        assert_embed = create_new_mod_channel_embed(channel)
        assert dpytest.verify().message().embed(embed=assert_embed)
        cleanup(dpytest.get_config().guilds[0].id, tf_cog, session)


@pytest.fixture
def text_filter_db_manager():
    return TextFilterDBManager(dpytest.get_config())


@pytest.mark.asyncio()
async def test_add_mod_channel_tag(text_filter_db_manager, tf_cog):
    with session_manager() as session:
        channel = dpytest.backend.make_text_channel(name="TestChannel", guild=dpytest.get_config().guilds[0])
        dpytest.get_config().channels.append(channel)

        await dpytest.message(koalabot.COMMAND_PREFIX + "setupModChannel <#" + str(channel.id) + ">")
        assert_embed = create_new_mod_channel_embed(channel)
        assert dpytest.verify().message().embed(embed=assert_embed)

        result = session.execute(select(TextFilterModeration.channel_id).filter_by(guild_id=channel.guild.id)).all()
        assert is_int(result[0][0])
        cleanup(dpytest.get_config().guilds[0].id, tf_cog, session)


@pytest.mark.asyncio()
async def test_add_mod_channel_empty():
    with pytest.raises(Exception):
        await dpytest.message(koalabot.COMMAND_PREFIX + "setupModChannel")


@pytest.mark.asyncio()
async def test_add_mod_channel_unrecognised_channel():
    with pytest.raises(Exception):
        await dpytest.message(koalabot.COMMAND_PREFIX + "setupModChannel 123")


@pytest.mark.asyncio()
async def test_add_mod_channel_too_many_arguments():
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=dpytest.get_config().guilds[0])
    dpytest.get_config().channels.append(channel)
    with pytest.raises(Exception):
        await dpytest.message(koalabot.COMMAND_PREFIX + "setupModChannel " + str(channel.id) + " a b c d e")


@pytest.mark.asyncio()
async def test_remove_mod_channel(tf_cog):
    with session_manager() as session:
        channel = dpytest.backend.make_text_channel(name="TestChannel", guild=dpytest.get_config().guilds[0])
        channel_id = str(channel.id)
        dpytest.get_config().channels.append(channel)

        await dpytest.message(koalabot.COMMAND_PREFIX + "setupModChannel " + channel_id)
        assert_embed = create_new_mod_channel_embed(channel)
        assert dpytest.verify().message().embed(embed=assert_embed)

        await dpytest.message(koalabot.COMMAND_PREFIX + "removeModChannel " + channel_id)
        assert_embed = remove_mod_channel_embed(channel)
        assert dpytest.verify().message().embed(embed=assert_embed)
        cleanup(dpytest.get_config().guilds[0].id, tf_cog, session)


@pytest.mark.asyncio()
async def test_remove_mod_channel_empty():
    with pytest.raises(Exception):
        await dpytest.message(koalabot.COMMAND_PREFIX + "removeModChannel")


@pytest.mark.asyncio()
async def test_remove_mod_channel_too_many_arguments():
    with pytest.raises(Exception):
        await dpytest.message(koalabot.COMMAND_PREFIX + "removeModChannel 123 a b c d e")


@pytest.mark.asyncio()
async def test_remove_mod_channel_unrecognised_channel():
    with pytest.raises(Exception):
        await dpytest.message(koalabot.COMMAND_PREFIX + "removeModChannel 123 a b c d e")


@pytest.mark.asyncio()
async def test_list_channels(tf_cog):
    with session_manager() as session:
        channel = dpytest.backend.make_text_channel(name="TestChannel", guild=dpytest.get_config().guilds[0])
        dpytest.get_config().channels.append(channel)

        await dpytest.message(koalabot.COMMAND_PREFIX + "setupModChannel " + str(channel.id))
        assert_embed = create_new_mod_channel_embed(channel)
        assert dpytest.verify().message().embed(embed=assert_embed)

        await dpytest.message(koalabot.COMMAND_PREFIX + "listModChannels")
        assert_embed = list_mod_channel_embed([channel])
        assert dpytest.verify().message().embed(embed=assert_embed)
        cleanup(dpytest.get_config().guilds[0].id, tf_cog, session)


@pytest.mark.asyncio()
async def test_list_multiple_channels(tf_cog):
    with session_manager() as session:
        channel1 = dpytest.backend.make_text_channel(name="TestChannel1", guild=dpytest.get_config().guilds[0])
        channel2 = dpytest.backend.make_text_channel(name="TestChannel2", guild=dpytest.get_config().guilds[0])
        dpytest.get_config().channels.append(channel1)
        dpytest.get_config().channels.append(channel2)

        await dpytest.message(koalabot.COMMAND_PREFIX + "setupModChannel " + str(channel1.id))
        assert_embed = create_new_mod_channel_embed(channel1)
        assert dpytest.verify().message().embed(embed=assert_embed)

        await dpytest.message(koalabot.COMMAND_PREFIX + "setupModChannel " + str(channel2.id))
        assert_embed = create_new_mod_channel_embed(channel2)
        assert dpytest.verify().message().embed(embed=assert_embed)

        await dpytest.message(koalabot.COMMAND_PREFIX + "listModChannels")
        assert_embed = list_mod_channel_embed([channel1, channel2])
        assert dpytest.verify().message().embed(embed=assert_embed)
        cleanup(dpytest.get_config().guilds[0].id, tf_cog, session)


@pytest.mark.asyncio()
async def test_ignore_channel(tf_cog):
    with session_manager() as session:
        channel1 = dpytest.backend.make_text_channel(name="TestChannel1", guild=dpytest.get_config().guilds[0])

        await dpytest.message(koalabot.COMMAND_PREFIX + "filter_word ignoreme")
        assert_filtered_confirmation("ignoreme", "banned")

        await dpytest.message(koalabot.COMMAND_PREFIX + "ignoreChannel " + channel1.mention)
        assert_new_ignore(channel1.mention)

        # Should be ignored
        await dpytest.message("ignoreme", channel=channel1)

        # Should be deleted and warned
        await dpytest.message("ignoreme")
        assert_banned_warning("ignoreme")

        cleanup(dpytest.get_config().guilds[0].id, tf_cog, session)


@pytest.mark.asyncio()
async def test_ignore_user(tf_cog):
    with session_manager() as session:
        message = await dpytest.message(koalabot.COMMAND_PREFIX + "filter_word ignoreuser")
        assert_filtered_confirmation("ignoreuser", "banned")

        # Should be deleted and warned
        await dpytest.message("ignoreuser")
        assert_banned_warning("ignoreuser")

        await dpytest.message(koalabot.COMMAND_PREFIX + "ignoreUser " + message.author.mention)
        assert_new_ignore(message.author.mention)

        # Should be ignored
        await dpytest.message("ignoreuser")
        cleanup(dpytest.get_config().guilds[0].id, tf_cog, session)


@pytest.mark.asyncio()
async def test_ignore_empty_user():
    with pytest.raises(Exception):
        await dpytest.message(koalabot.COMMAND_PREFIX + "ignoreUser")


@pytest.mark.asyncio()
async def test_unignore_channel():
    await dpytest.message(koalabot.COMMAND_PREFIX + "filter_word ignoreuser")
    assert_filtered_confirmation("ignoreuser", "banned")

    await dpytest.message(
        koalabot.COMMAND_PREFIX + "ignoreChannel " + dpytest.get_config().guilds[0].channels[0].mention)
    assert_new_ignore(dpytest.get_config().guilds[0].channels[0].mention)

    # Should be ignored
    await dpytest.message("ignoreuser")

    await dpytest.message(koalabot.COMMAND_PREFIX + "unignore " + dpytest.get_config().guilds[0].channels[0].mention)
    assert_remove_ignore(dpytest.get_config().guilds[0].channels[0].mention)

    # Should be deleted and warned
    await dpytest.message("ignoreuser")
    assert_banned_warning("ignoreuser")


@pytest.mark.asyncio()
async def test_list_ignored():
    mes = await dpytest.message(
        koalabot.COMMAND_PREFIX + "ignoreChannel " + dpytest.get_config().guilds[0].channels[0].mention)
    assert_new_ignore(dpytest.get_config().guilds[0].channels[0].mention)

    await dpytest.message(koalabot.COMMAND_PREFIX + "ignoreUser " + mes.author.mention)
    assert_new_ignore(mes.author.mention)

    await dpytest.message(koalabot.COMMAND_PREFIX + "listIgnored")
    assert list_ignored_embed([dpytest.get_config().guilds[0].channels[0], mes.author])
