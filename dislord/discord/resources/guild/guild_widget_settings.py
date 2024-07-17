from dislord.types import ObjDict
from dislord.discord.reference import Snowflake


class GuildWidgetSettings(ObjDict):
    enabled: bool
    channel_id: Snowflake | None
