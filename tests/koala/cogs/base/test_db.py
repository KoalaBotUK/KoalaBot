import datetime

import discord
from sqlalchemy import select

from koala.cogs.base import db
from koala.cogs.base.models import ScheduledActivities


def test_add_scheduled_activity(session):
    activity_type = discord.ActivityType.streaming
    message = "NUEL finals"
    url = "https://twitch.tv/thenuel"
    time_start = datetime.datetime.fromisoformat("2020-01-01 00:00:00")
    time_end = datetime.datetime.fromisoformat("2021-01-01 00:00:00")

    db.add_scheduled_activity(activity_type, message, url, time_start, time_end, session=session)

    results = session.execute(select(ScheduledActivities)).scalars().all()
    assert len(results) == 1
    result = results[0]
    assert result.message == "NUEL finals"
    assert result.time_end == time_end


def test_add_scheduled_activity_no_url(session):
    activity_type = discord.ActivityType.streaming
    message = "NUEL finals"
    url = None
    time_start = datetime.datetime.fromisoformat("2020-01-01 00:00:00")
    time_end = datetime.datetime.fromisoformat("2021-01-01 00:00:00")

    db.add_scheduled_activity(activity_type, message, url, time_start, time_end, session=session)

    results = session.execute(select(ScheduledActivities)).scalars().all()
    assert len(results) == 1
    result = results[0]
    assert result.message == "NUEL finals"
    assert result.stream_url is None


def test_get_scheduled_activities(session):
    activity_type = discord.ActivityType.streaming
    message = "NUEL finals"
    url = None
    time_start = datetime.datetime.fromisoformat("2020-01-01 00:00:00")
    time_end = datetime.datetime.fromisoformat("2021-01-01 00:00:00")

    db.add_scheduled_activity(activity_type, message, url, time_start, time_end, session=session)

    assert len(db.get_scheduled_activities(False, False)) == 1


def test_remove_scheduled_activities(session):
    activity_type = discord.ActivityType.streaming
    message = "NUEL finals"
    url = None
    time_start = datetime.datetime.fromisoformat("2020-01-01 00:00:00")
    time_end = datetime.datetime.fromisoformat("2021-01-01 00:00:00")

    db.add_scheduled_activity(activity_type, message, url, time_start, time_end, session=session)

    db.remove_scheduled_activities(1)

    assert len(db.get_scheduled_activities(False, False)) == 0
   
