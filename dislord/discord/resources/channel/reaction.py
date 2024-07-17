from dislord.types import ObjDict
from dislord.model.base import BaseModel, HexColor
from dislord.discord.resources.channel.reaction_count_details import ReactionCountDetails
from dislord.discord.resources.emoji.emoji import PartialEmoji


class Reaction(ObjDict):
    count: int
    count_details: ReactionCountDetails
    me: bool
    me_burst: bool
    emoji: PartialEmoji
    bust_colors: list[HexColor]
