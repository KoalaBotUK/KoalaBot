import datetime

import discord
import mock
import pytest
from discord.ext import commands
import discord.ext.test as dpytest
from sqlalchemy import null

import koalabot
from koala.cogs.base import core


@pytest.fixture
def reset_extensions(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    core.disable_extension(bot, guild.id, "All")


def test_activity_clear_current():
    core.current_activity = "test"
    assert core.current_activity
    core.activity_clear_current()
    assert not core.current_activity


@pytest.mark.asyncio
async def test_activity_set(bot: commands.Bot):
    await core.activity_set(discord.ActivityType.watching, "you", None, bot)
    assert dpytest.verify().activity().matches(discord.Activity(type=discord.ActivityType.watching, name="you"))


@pytest.mark.asyncio
async def test_activity_set_current_scheduled(bot: commands.Bot, session):
    core.activity_schedule(discord.ActivityType.watching, "you2", None,
                           datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(days=1))
    await core.activity_set_current_scheduled(bot, session=session)
    assert dpytest.verify().activity().matches(discord.Activity(type=discord.ActivityType.watching, name="you2"))


def test_activity_list():
    core.activity_schedule(discord.ActivityType.watching, "you2", None,
                           datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(days=1))
    schedule = core.activity_list(True)
    assert schedule[0].activity_id == 1
    assert schedule[0].activity_type == discord.ActivityType.watching
    assert schedule[0].message == "you2"
    

async def test_remove_scheduled_activity():
    core.activity_schedule(discord.ActivityType.watching, "you2", None,
                           datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(days=1))
    assert core.activity_list(True)[0].activity_id == 1
    
    core.activity_remove(1)
    assert not core.activity_list(True)


@pytest.mark.asyncio
async def test_ping(bot: commands.Bot):
    with mock.patch('discord.client.Client.latency', new_callable=mock.PropertyMock) as mock_last_transaction:
        mock_last_transaction.return_value = 0.42
        resp = await core.ping(bot)
        assert "Pong! 420ms" in resp


def test_support_link():
    resp = core.support_link()
    assert "Join our support server for more help! https://discord.gg/5etEjVd" in resp


def test_version():
    resp = core.get_version()
    assert f"version: {koalabot.__version__}" in resp


@pytest.mark.asyncio
async def test_purge(bot: commands.Bot):
    channel: discord.TextChannel = dpytest.get_config().channels[0]
    with mock.patch.object(discord.TextChannel, 'purge') as mock1:
        await core.purge(bot, channel.id, 2)
    mock1.assert_called_with(3)

# Load cogs

@mock.patch("koalabot.ENABLED_COGS", ['announce'])
@pytest.mark.asyncio
async def test_load_cog(bot: commands.Bot):
    resp = await core.load_cog(bot, "announce", "koala.cogs")
    assert resp == "announce Cog Loaded"


@pytest.mark.asyncio
async def test_load_base_cog(bot: commands.Bot):
    resp = await core.load_cog(bot, "base", "koala.cogs")
    assert resp == "base Cog Loaded"


@pytest.mark.asyncio
async def test_load_invalid_cog(bot: commands.Bot):
    with pytest.raises(discord.ext.commands.errors.ExtensionNotFound, match="Extension 'koala.cogs.FakeCog' could not be loaded."):
        await core.load_cog(bot, "FakeCog", "koala.cogs")


@mock.patch("koalabot.ENABLED_COGS", ['announce'])
@pytest.mark.asyncio
async def test_load_already_loaded_cog(bot: commands.Bot):
    await core.load_cog(bot, "announce", "koala.cogs")
    with pytest.raises(discord.ext.commands.errors.ExtensionAlreadyLoaded, match="Extension 'koala.cogs.announce' is already loaded"):
        await core.load_cog(bot, "announce", "koala.cogs")

# Unload cogs

@pytest.mark.asyncio
async def test_unload_cog(bot: commands.Bot):
    await core.load_cog(bot, "announce", "koala.cogs")
    resp = await core.unload_cog(bot, "announce", "koala.cogs")
    assert resp == "announce Cog Unloaded"


@pytest.mark.asyncio
async def test_unload_base_cog(bot: commands.Bot):
    with pytest.raises(discord.ext.commands.errors.ExtensionError, match="Sorry, you can't unload the base cog"):
        await core.unload_cog(bot, "base", "koala.cogs")


@pytest.mark.asyncio
async def test_unload_not_loaded_cog(bot: commands.Bot):
    with pytest.raises(discord.ext.commands.errors.ExtensionNotLoaded, match="Extension 'koala.cogs.announce' has not been loaded."):
        await core.unload_cog(bot, "announce", "koala.cogs")


@pytest.mark.asyncio
async def test_unload_invalid_cog(bot: commands.Bot):
    with pytest.raises(discord.ext.commands.errors.ExtensionNotLoaded, match="Extension 'koala.cogs.FakeCog' has not been loaded."):
        await core.unload_cog(bot, "FakeCog", "koala.cogs")

# Enable extensions

@mock.patch("koalabot.ENABLED_COGS", ["Announce"])
@pytest.mark.asyncio
async def test_enable_extension(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    await test_load_cog(bot)
    embed = await core.enable_extension(bot, guild.id, "Announce")
    assert embed.title == "Announce enabled"


@pytest.mark.asyncio
async def test_enable_extension_all(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    embed = await core.enable_extension(bot, guild.id, "All")
    assert embed.title == "All extensions enabled"


@pytest.mark.asyncio
async def test_enable_invalid_extension(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    with pytest.raises(NotImplementedError, match="InvalidExtension is not a valid extension"):
        await core.enable_extension(bot, guild.id, "InvalidExtension")

# Disable extensions

@mock.patch("koalabot.ENABLED_COGS", ["announce"])
@pytest.mark.asyncio
async def test_disable_extension(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    await test_enable_extension(bot)
    embed = await core.disable_extension(bot, guild.id, "Announce")
    assert embed.title == "Announce disabled"


@pytest.mark.asyncio
async def test_disable_extension_all(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    await test_enable_extension_all(bot)
    embed = await core.disable_extension(bot, guild.id, "All")
    assert embed.title == "All disabled"
    

@pytest.mark.asyncio
async def test_disable_extension_not_enabled(bot: commands.Bot):
    with pytest.raises(NotImplementedError, match="Announce is not an enabled extension"):
        guild: discord.Guild = dpytest.get_config().guilds[0]
        await core.disable_extension(bot, guild.id, "Announce")


@pytest.mark.asyncio
async def test_disable_invalid_extension(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    with pytest.raises(NotImplementedError, match="InvalidExtension is not an enabled extension"):
        await core.disable_extension(bot, guild.id, "InvalidExtension")

# List enabled extensions

@mock.patch("koalabot.ENABLED_COGS", ["announce"])
@pytest.mark.asyncio
async def test_list_enabled_extensions(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    await test_enable_extension(bot)
    embed = await core.list_enabled_extensions(guild.id)
    assert embed.fields[0].name == ":white_check_mark: Enabled"
    assert "Announce" in embed.fields[0].value

# Get available extensions

@mock.patch("koalabot.COGS_PACKAGE", koalabot.COGS_PACKAGE)
@mock.patch("koalabot.ENABLED_COGS", ["announce"])
@pytest.mark.asyncio
async def test_get_extensions(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    resp = core.get_all_available_guild_extensions(guild.id)
    print(resp)
    assert resp[0] == "Announce"