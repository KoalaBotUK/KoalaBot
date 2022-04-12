import datetime
from typing import List, Optional

import discord
import sqlalchemy.orm
from sqlalchemy import select

from koala.cogs.base.models import ScheduledActivities
from koala.db import assign_session


@assign_session
def add_scheduled_activity(activity_type: discord.ActivityType, message: str, url: Optional[str],
                           time_start: datetime.datetime, time_end: datetime.datetime,
                           session: sqlalchemy.orm.Session) -> ScheduledActivities:
    """
    Add scheduled activity to database
    :param activity_type:
    :param message:
    :param url:
    :param time_start:
    :param time_end:
    :param session:
    :return:
    """
    activity = ScheduledActivities(activity_type=activity_type, message=message, stream_url=url, time_start=time_start,
                                   time_end=time_end)
    session.add(activity)
    session.commit()
    return activity


@assign_session
def get_scheduled_activities(start_time_restricted: bool, end_time_restricted: bool,
                             session: sqlalchemy.orm.Session) -> List[ScheduledActivities]:
    """
    Get all scheduled activities
    :param start_time_restricted:
    :param end_time_restricted:
    :param session:
    :return:
    """
    current_time = datetime.datetime.now()
    query = select(ScheduledActivities)
    if start_time_restricted:
        query = query.where(ScheduledActivities.time_start < current_time)
    if end_time_restricted:
        query = query.where(ScheduledActivities.time_end > current_time)

    return session.execute(query).scalars().all()


@assign_session
def remove_scheduled_activities(activity_id: int, session: sqlalchemy.orm.Session) -> ScheduledActivities:
    """
    Delete a specified scheduled activity from a database
    :param activity_id:
    :param session:
    :return:
    """
    activity = session.execute(select(ScheduledActivities).filter_by(activity_id=activity_id)).scalar()
    session.delete(activity)
    session.commit()
    return activity
