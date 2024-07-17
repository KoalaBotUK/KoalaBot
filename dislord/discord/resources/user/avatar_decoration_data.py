from dislord.types import ObjDict
from dislord.discord.reference import Snowflake


class AvatarDecorationData(ObjDict):
    asset: str
    sku_id: Snowflake
