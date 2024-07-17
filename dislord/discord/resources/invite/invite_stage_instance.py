from dislord.types import ObjDict
from dislord.discord.resources.guild.guild_member import PartialGuildMember


class InviteStageInstance(ObjDict):
    members: list[PartialGuildMember]
    participant_count: int
    speaker_count: int
    topic: str
