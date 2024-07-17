from dislord.types import ObjDict
from dislord.discord.resources.sticker.sticker import Sticker
from dislord.discord.reference import Snowflake, Missing


class StickerPack(ObjDict):
    id: Snowflake
    stickers: list[Sticker]
    name: str
    sku_id: Snowflake
    cover_sticker_id: Snowflake | Missing
    description: str
    banner_asset_id: Snowflake | Missing
