from enum import IntEnum

from dislord.types import ObjDict
from dislord.discord.reference import Snowflake
from dislord.discord.resources.user.user import PartialUser
from dislord.discord.topics.teams.team_member_roles import TeamMemberRoleType


class MembershipState(IntEnum):
    INVITED = 1
    ACCEPTED = 2


class TeamMember(ObjDict):
    membership_state: int
    team_id: Snowflake
    user: PartialUser
    role: TeamMemberRoleType


class Team(ObjDict):
    icon: str | None
    id: Snowflake
    members: list[TeamMember]
    name: str
    owner_user_id: Snowflake
