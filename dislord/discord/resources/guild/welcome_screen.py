from dislord.types import ObjDict
from dislord.discord.reference import Snowflake


class WelcomeScreenChannel(ObjDict):
    channel_id: Snowflake
    description: str
    emoji_id: Snowflake | None
    emoji_name: str | None


class WelcomeScreen(ObjDict):
    description: str | None
    welcome_channel: list[WelcomeScreenChannel]
