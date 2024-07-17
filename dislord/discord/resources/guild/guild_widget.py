from dislord.types import ObjDict
from dislord.discord.resources.channel.channel import PartialChannel
from dislord.discord.resources.user.user import PartialUser
from dislord.discord.reference import Snowflake


class GuildWidget(ObjDict):
    id: Snowflake
    name: str
    instant_invite: str | None
    channels: list[PartialChannel]
    members: list[PartialUser]
    presence_count: int
