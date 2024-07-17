from dislord.types import ObjDict


class PollAnswerCount(ObjDict):
    id: int
    count: int
    me_voted: bool


class PollResults(ObjDict):
    is_finalized: bool
    answer_counts: list[PollAnswerCount]
