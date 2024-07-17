from dislord.types import ObjDict
from dislord.discord.resources.sticker.sticker import StickerFormatType
from dislord.discord.reference import Snowflake


class StickerItem(ObjDict):
    id: Snowflake
    name: str
    format_type: StickerFormatType
