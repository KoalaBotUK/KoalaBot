from enum import IntEnum

from dislord.types import ObjDict
from dislord.discord.resources.application.models import PartialApplication
from dislord.discord.resources.channel.channel import PartialChannel
from dislord.discord.resources.guild.guild import PartialGuild
from dislord.discord.resources.guild_scheduled_event.guild_scheduled_event import GuildScheduledEvent
from dislord.discord.resources.invite.invite_stage_instance import InviteStageInstance
from dislord.discord.resources.user.user import User
from dislord.discord.reference import Missing, ISOTimestamp


class InviteTargetType(IntEnum):
    STREAM = 1
    EMBEDDED_APPLICATION = 2


class InviteType(IntEnum):
    GUILD = 0
    GROUP_DM = 1
    FRIEND = 2


class Invite(ObjDict):
    type: InviteType
    code: str
    guild: PartialGuild | Missing
    channel: PartialChannel | None
    inviter: User | Missing
    target_type: InviteTargetType | Missing
    target_user: User | Missing
    target_application: PartialApplication | Missing
    approximate_presence_count = int | Missing
    approximate_member_count: int | Missing
    expires_at: ISOTimestamp | Missing | None
    stage_instance: InviteStageInstance | Missing
    guild_scheduled_event: GuildScheduledEvent | Missing
