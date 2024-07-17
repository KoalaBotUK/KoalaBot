from enum import IntFlag

from dislord.types import ObjDict
from dislord.discord.reference import Snowflake, Missing


class AttachmentFlag(IntFlag):
    IS_REMIX = 1 << 2


class PartialAttachment(ObjDict):
    id: Snowflake
    filename: str
    description: str | Missing


class Attachment(PartialAttachment):
    content_type: str | Missing
    size: int
    url: str
    proxy_url: str
    height: int | Missing | None
    width: int | Missing | None
    ephemeral: bool | Missing
    duration_secs: float | Missing
    waveform: str | Missing
    flags: AttachmentFlag
