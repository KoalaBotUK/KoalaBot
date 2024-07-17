from dislord.types import ObjDict
from dislord.discord.resources.guild.guild_member import GuildMember
from dislord.discord.resources.user.user import User
from dislord.discord.reference import Snowflake, Missing


class GuildScheduledEventUser(ObjDict):
    guild_scheduled_event_id: Snowflake
    user: User
    member: GuildMember | Missing
