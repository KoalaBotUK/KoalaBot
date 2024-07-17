from dislord.types import ObjDict


class VoiceRegion(ObjDict):
    id: str
    name: str
    optimal: bool
    deprecated: bool
    custom: bool
