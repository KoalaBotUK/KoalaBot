
from dislord.types import ObjDict
from dislord.discord.resources.user.user import User


class Ban(ObjDict):
    reason: str | None
    user: User
