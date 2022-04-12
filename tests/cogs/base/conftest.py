import pytest
from sqlalchemy import delete

from koala.cogs.base.models import ScheduledActivities


@pytest.fixture(autouse=True)
def delete_tables(session):
    session.execute(delete(ScheduledActivities))
    session.commit()
