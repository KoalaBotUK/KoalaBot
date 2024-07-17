from dislord.types import ObjDict
from dislord.discord.resources.channel.channel import ChannelType
from dislord.discord.reference import Snowflake


class ChannelMention(ObjDict):
    id: Snowflake
    guild_id: Snowflake
    type: ChannelType
    name: str
