from dislord.discord.reference import Missing
from dislord.discord.resources.poll.layout_type import LayoutType
from dislord.discord.resources.poll.poll_answer import PollAnswer
from dislord.discord.resources.poll.poll_media import PollMedia
from dislord.types import ObjDict


class PollCreateRequest(ObjDict):
    question: PollMedia
    answers: list[PollAnswer]
    duration: int
    allow_multiset: bool
    layout_type: LayoutType | Missing
