import datetime
from typing import List

import discord
import sqlalchemy.orm
from sqlalchemy import select

from koala.cogs.base.models import ScheduledActivities
from koala.db import assign_session


@assign_session
def add_scheduled_activity(activity_type: discord.ActivityType, message: str, url: str,
                           time_start: datetime.datetime, time_end: datetime.datetime,
                           session: sqlalchemy.orm.Session) -> None:
    activity = ScheduledActivities(activity_type=activity_type, message=message, stream_url=url, time_start=time_start,
                                   time_end=time_end)
    session.add(activity)
    session.commit()


@assign_session
def get_scheduled_activities(start_time_restricted: bool, end_time_restricted: bool,
                             session: sqlalchemy.orm.Session) -> List[ScheduledActivities]:
    current_time = datetime.datetime.now()
    query = select(ScheduledActivities)
    if start_time_restricted:
        query = query.where(ScheduledActivities.time_start < current_time)
    if end_time_restricted:
        query = query.where(ScheduledActivities.time_end > current_time)

    return session.execute(query).scalars().all()


@assign_session
def remove_scheduled_activities(activity_id: int, session: sqlalchemy.orm.Session) -> ScheduledActivities:
    activity = session.execute(select(ScheduledActivities).filter_by(activity_id=activity_id)).scalar()
    session.delete(activity)
    session.commit()
    return activity
