from dislord.types import ObjDict
from dislord.discord.reference import ISOTimestamp, Missing


class ThreadMetadata(ObjDict):
    archived: bool
    auto_archive_duration: int
    archive_timestamp: ISOTimestamp
    locked: bool
    invitable: bool | Missing
    create_timestamp: ISOTimestamp | Missing | None
