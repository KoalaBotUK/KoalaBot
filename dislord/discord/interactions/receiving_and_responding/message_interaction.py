from enum import Enum

from dislord.types import ObjDict
from dislord.discord.resources.guild.guild_member import PartialGuildMember
from dislord.discord.resources.user.user import User
from dislord.discord.reference import Missing, Snowflake


class InteractionType(Enum):
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5


class MessageInteraction(ObjDict):
    id: Snowflake
    type: InteractionType
    name: str
    user: User
    member: PartialGuildMember | Missing
