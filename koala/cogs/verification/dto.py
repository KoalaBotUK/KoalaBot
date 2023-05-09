from dataclasses import dataclass
from typing import List

from koala.cogs.verification.models import Roles


@dataclass
class VerifyRole:
    email_suffix: str
    role_id: int

    @staticmethod
    def from_db_roles(roles: Roles):
        return VerifyRole(roles.email_suffix, roles.r_id)


@dataclass
class VerifyConfig:
    guild_id: str
    roles: List[VerifyRole]


