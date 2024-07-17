from enum import Enum


class TeamMemberRoleType(Enum):
    OWNER = None
    ADMIN = "admin"
    DEVELOPER = "developer"
    READ_ONLY = "read_only"
