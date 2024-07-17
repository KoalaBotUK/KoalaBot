from dislord.types import ObjDict
from dislord.discord.resources.emoji.emoji import PartialEmoji
from dislord.discord.reference import Missing


class PollMedia(ObjDict):
    text: str | Missing
    emoji: PartialEmoji | Missing
