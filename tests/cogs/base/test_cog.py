#!/usr/bin/env python

"""
Testing KoalaBot BaseCog

Commented using reStructuredText (reST)
"""
import datetime

# Futures

# Built-in/Generic Imports

# Libs
import discord
import discord.ext.test as dpytest
import mock
import pytest
import pytest_asyncio
from discord.ext import commands
from sqlalchemy import delete

# Own modules
import koalabot
from koala.cogs import BaseCog
from koala.cogs.base.cog import setup as setup_cog, BaseCog
from koala.db import session_manager
from koala.colours import KOALA_GREEN
from koala.models import KoalaExtensions, GuildExtensions
from koala.transformers import DatetimeTransformer


# Constants

# Variables


@pytest.fixture(scope='session', autouse=True)
def setup_is_dpytest():
    koalabot.is_dpytest = True
    yield
    koalabot.is_dpytest = False


@pytest_asyncio.fixture(name='base_cog', scope='function', autouse=True)
async def base_cog_fixture(bot: commands.Bot):
    """ setup any state specific to the execution of the given module."""
    cog = BaseCog(bot)
    await bot.add_cog(cog)
    await dpytest.empty_queue()
    dpytest.configure(bot)
    return cog


@mock.patch("koalabot.COGS_PACKAGE", "tests.tests_utils.fake_load_all_cogs")
@mock.patch("koalabot.ENABLED_COGS", [])
@pytest.mark.asyncio
async def test_list_koala_ext_disabled(base_cog: BaseCog, mock_interaction):
    await koalabot.load_all_cogs(base_cog.bot)
    await base_cog.list_koala_ext.callback(base_cog, mock_interaction)
    expected_embed = discord.Embed()
    expected_embed.title = "Enabled extensions"
    expected_embed.colour = KOALA_GREEN
    expected_embed.add_field(name=":negative_squared_cross_mark: Disabled", value="Greetings\n")
    expected_embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    mock_interaction.response.assert_eq(embed=expected_embed)


@mock.patch("koalabot.COGS_PACKAGE", "tests.tests_utils.fake_load_all_cogs")
@mock.patch("koalabot.ENABLED_COGS", ['greetings_cog'])
@pytest.mark.asyncio
async def test_enable_koala_ext(base_cog: BaseCog, mock_interaction):
    await koalabot.load_all_cogs(base_cog.bot)
    await base_cog.enable_koala_ext.callback(base_cog, mock_interaction, "Greetings")
    expected_embed = discord.Embed()
    expected_embed.title = "Greetings enabled"
    expected_embed.colour = KOALA_GREEN
    expected_embed.add_field(name=":white_check_mark: Enabled", value="Greetings\n")
    expected_embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    mock_interaction.response.assert_eq(embed=expected_embed)


@mock.patch("koalabot.COGS_PACKAGE", "tests.tests_utils.fake_load_all_cogs")
@mock.patch("koalabot.ENABLED_COGS", ['greetings_cog'])
@pytest.mark.asyncio
async def test_disable_koala_ext(base_cog: BaseCog, mock_interaction):
    await test_enable_koala_ext(base_cog, mock_interaction)
    await base_cog.disable_koala_ext.callback(base_cog, mock_interaction, "Greetings")
    expected_embed = discord.Embed()
    expected_embed.title = "Greetings disabled"
    expected_embed.colour = KOALA_GREEN
    expected_embed.add_field(name=":negative_squared_cross_mark: Disabled", value="Greetings\n")
    expected_embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    mock_interaction.response.assert_eq(embed=expected_embed)


@pytest.mark.asyncio
async def test_on_ready(base_cog: BaseCog):
    await base_cog.on_ready()
    assert dpytest.verify().activity().matches(discord.Activity(type=discord.ActivityType.playing,
                                                                name=koalabot.COMMAND_PREFIX + "help koalabot.uk"))


@pytest.mark.asyncio
async def test_activity(base_cog: BaseCog, mock_interaction):
    await base_cog.activity_set.callback(base_cog,
                                         interaction=mock_interaction,
                                         activity=discord.ActivityType.watching,
                                         message="you")
    assert dpytest.verify().activity().matches(discord.Activity(type=discord.ActivityType.watching, name="you"))
    mock_interaction.response.assert_eq("I am now watching you", ephemeral=True)


@pytest.mark.asyncio
async def test_schedule_activity(base_cog: BaseCog, mock_interaction):
    await base_cog.activity_schedule.callback(base_cog,
                                              interaction=mock_interaction,
                                              activity=discord.ActivityType.playing,
                                              message="test",
                                              start_time=await DatetimeTransformer().transform(
                                                  mock_interaction, "2020-01-01 00:00:00"),
                                              end_time=await DatetimeTransformer().transform(
                                                  mock_interaction, "2020-01-01 01:00:00"))
    mock_interaction.response.assert_eq("Activity saved", ephemeral=True)


@pytest.mark.asyncio
async def test_list_activity(base_cog: BaseCog, mock_interaction):
    await test_schedule_activity(base_cog, mock_interaction)
    await base_cog.activity_list.callback(base_cog, mock_interaction)
    mock_interaction.response.assert_eq("Activities:")


@pytest.mark.asyncio
async def test_list_activity_show_all(base_cog: BaseCog, mock_interaction):
    await test_schedule_activity(base_cog, mock_interaction)
    await base_cog.activity_list.callback(base_cog, mock_interaction, True)
    mock_interaction.response.assert_eq("Activities:"
                                        "\n1, playing, None, test, 2020-01-01 00:00:00, 2020-01-01 01:00:00")


@pytest.mark.asyncio
async def test_remove_activity(base_cog: BaseCog, mock_interaction):
    await test_list_activity_show_all(base_cog, mock_interaction)
    await base_cog.activity_remove.callback(base_cog, mock_interaction, 1)
    mock_interaction.response.assert_eq("Removed:"
                                        "\n1, playing, None, test, 2020-01-01 00:00:00, 2020-01-01 01:00:00")
    await base_cog.activity_list.callback(base_cog, mock_interaction, True)
    mock_interaction.response.assert_eq("Activities:")


@mock.patch("builtins.round", mock.MagicMock(return_value=4))
@pytest.mark.asyncio
async def test_ping(base_cog: BaseCog, mock_interaction):
    await base_cog.ping.callback(base_cog, mock_interaction)
    mock_interaction.response.assert_eq("Pong! 4ms", ephemeral=True)


@pytest.mark.asyncio
async def test_support(base_cog: BaseCog, mock_interaction):
    await base_cog.support.callback(base_cog, mock_interaction)
    mock_interaction.response.assert_eq("Join our support server for more help! https://discord.gg/5etEjVd")


@pytest.mark.asyncio
async def test_default_clear(base_cog: BaseCog, mock_interaction):
    with mock.patch.object(discord.TextChannel, 'purge') as mock1:
        await base_cog.clear.callback(base_cog, mock_interaction)
    mock1.assert_called_with(limit=2)


@pytest.mark.asyncio
async def test_clear(base_cog: BaseCog, mock_interaction):
    with mock.patch.object(discord.TextChannel, 'purge') as mock1:
        await base_cog.clear.callback(base_cog, mock_interaction, 4)
    mock1.assert_called_with(limit=5)


@pytest.mark.asyncio
async def test_load_cog(base_cog: BaseCog, mock_interaction):
    with mock.patch.object(discord.ext.commands.bot.Bot, 'load_extension') as mock1:
        await base_cog.load_cog.callback(base_cog, mock_interaction, "base")
    mock1.assert_called_with(".base", package="koala.cogs")


@pytest.mark.asyncio
async def test_invalid_load_cog(base_cog: BaseCog, mock_interaction):
    with pytest.raises(commands.ExtensionError,
                       match="Extension 'koala.cogs.FakeCog' could not be loaded."):
        await base_cog.load_cog.callback(base_cog, mock_interaction, "FakeCog")


@pytest.mark.asyncio
async def test_unload_base_cog(base_cog: BaseCog, mock_interaction):
    with pytest.raises(commands.ExtensionError, match="Sorry, you can't unload the base cog"):
        await base_cog.unload_cog.callback(base_cog, mock_interaction, "BaseCog")


@mock.patch("koalabot.COGS_PACKAGE", "tests.tests_utils.fake_load_all_cogs")
@pytest.mark.asyncio
async def test_load_valid_cog(base_cog: BaseCog, mock_interaction):
    with mock.patch.object(discord.ext.commands.bot.Bot, 'load_extension') as mock1:
        await base_cog.load_cog.callback(base_cog, mock_interaction, "Greetings")
    mock1.assert_called_with(".Greetings", package="tests.tests_utils.fake_load_all_cogs")


@mock.patch("koalabot.COGS_PACKAGE", "tests.tests_utils.fake_load_all_cogs")
@pytest.mark.asyncio
async def test_load_and_unload_valid_cog(base_cog: BaseCog, mock_interaction):
    with mock.patch.object(discord.ext.commands.bot.Bot, 'load_extension') as mock1:
        await base_cog.load_cog.callback(base_cog, mock_interaction, "Greetings")
    mock1.assert_called_with(".Greetings", package="tests.tests_utils.fake_load_all_cogs")

    with mock.patch.object(discord.ext.commands.bot.Bot, 'unload_extension') as mock1:
        await base_cog.unload_cog.callback(base_cog, mock_interaction, "Greetings")
    mock1.assert_called_with(".Greetings", package="tests.tests_utils.fake_load_all_cogs")


@pytest.mark.asyncio
async def test_invalid_unload_cog(base_cog: BaseCog, mock_interaction):
    with pytest.raises(commands.ExtensionNotLoaded,
                       match="Extension 'koala.cogs.FakeCog' has not been loaded."):
        await base_cog.unload_cog.callback(base_cog, mock_interaction, "FakeCog")


@pytest.mark.asyncio
async def test_version(base_cog: BaseCog, mock_interaction):
    await base_cog.version.callback(base_cog, mock_interaction)
    mock_interaction.response.assert_eq("version: " + koalabot.__version__)


@pytest.mark.asyncio
async def test_setup(bot):
    with mock.patch.object(discord.ext.commands.bot.Bot, 'add_cog') as mock1:
        await setup_cog(bot)
    mock1.assert_called()
