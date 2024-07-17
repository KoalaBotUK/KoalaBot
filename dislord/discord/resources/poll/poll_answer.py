from dislord.types import ObjDict
from dislord.discord.resources.poll.poll_media import PollMedia


class PollAnswer(ObjDict):
    answer_id: int
    poll_media: PollMedia
