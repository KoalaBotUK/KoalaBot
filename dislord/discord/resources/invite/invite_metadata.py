from dislord.types import ObjDict
from dislord.discord.reference import ISOTimestamp


class InviteMetadata(ObjDict):
    uses: int
    max_uses: int
    max_age: int
    temporary: bool
    created_at: ISOTimestamp
