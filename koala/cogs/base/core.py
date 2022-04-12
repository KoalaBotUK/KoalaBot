import datetime
from typing import List, Optional

import discord
from discord.ext.commands import Bot

from . import db
from .log import logger
from .models import ScheduledActivities
from koala.db import assign_session
from .utils import DEFAULT_ACTIVITY, activity_eq

# Constants

# Variables
current_activity = None


def activity_clear_current():
    global current_activity
    current_activity = None


async def activity_set(activity_type: discord.ActivityType, name: str, url: Optional[str], bot: Bot):
    """
    Set presence for this bot to the given presence
    :param activity_type:
    :param name:
    :param url:
    :param bot: 
    :return:
    """
    new_activity = discord.Activity(type=activity_type, name=name, url=url)
    await bot.change_presence(activity=new_activity)


@assign_session
def activity_schedule(activity_type: discord.ActivityType, message: str, url: Optional[str], start_time: datetime.datetime,
                      end_time: datetime.datetime, **kwargs):
    """
    Schedule an activity to be used for a timed presence
    :param activity_type:
    :param message:
    :param url:
    :param start_time:
    :param end_time:
    :param kwargs:
    :return:
    """
    db.add_scheduled_activity(activity_type, message, url, start_time, end_time, **kwargs)


@assign_session
def activity_list(show_all: bool, **kwargs) -> List[ScheduledActivities]:
    """
    Get a list of all scheduled activity
    :param show_all:
    :param kwargs:
    :return:
    """
    return db.get_scheduled_activities(False, not show_all, **kwargs)


@assign_session
def activity_remove(activity_id: int, **kwargs) -> ScheduledActivities:
    """
    Remove a scheduled activity
    :param activity_id:
    :param kwargs:
    :return:
    """
    return db.remove_scheduled_activities(activity_id, **kwargs)


@assign_session
async def activity_set_current_scheduled(bot: Bot, **kwargs):
    """
    Set the current scheduled activity as the bot presence
    :param bot:
    :param kwargs:
    :return:
    """
    activities = db.get_scheduled_activities(True, True, **kwargs)
    if len(activities) > 1:
        logger.warn("Multiple activities found for this timeslot, %s" % activities)

    if len(activities) != 0:
        activity = activities[0]
        new_activity = discord.Activity(
            type=activity.activity_type, name=activity.message, url=activity.stream_url)
    else:
        new_activity = DEFAULT_ACTIVITY

    global current_activity
    if not activity_eq(new_activity, current_activity):
        await bot.change_presence(activity=new_activity)
        logger.info("Auto changing bot presence: %s" % new_activity)
        current_activity = new_activity
