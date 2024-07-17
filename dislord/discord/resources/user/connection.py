from enum import IntEnum

from dislord.types import ObjDict
from dislord.discord.resources.guild.integration import Integration
from dislord.discord.reference import Missing


class VisibilityType(IntEnum):
    NONE = 0
    EVERYONE = 1


class Connection(ObjDict):
    id: str
    name: str
    type: str
    revoked: bool | Missing
    integrations: list[Integration] | Missing
    verified: bool
    friend_sync: bool
    show_activity: bool
    two_way_link: bool
    visibility: VisibilityType
