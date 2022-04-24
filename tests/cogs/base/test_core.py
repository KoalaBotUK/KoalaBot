import datetime

import discord
import pytest
from discord.ext import commands
import discord.ext.test as dpytest

from koala.cogs.base import core


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
