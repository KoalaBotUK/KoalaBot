from dislord.types import ObjDict
from dislord.discord.reference import Missing, ISOTimestamp


class EmbedField(ObjDict):
    name: str
    value: str
    inline: bool | Missing


class EmbedFooter(ObjDict):
    text: str
    icon_url: str | Missing
    proxy_icon_url: str | Missing


class EmbedAuthor(ObjDict):
    name: str
    url: str | Missing
    icon_url: str | Missing
    proxy_icon_url: str | Missing


class EmbedProvider(ObjDict):
    name: str | Missing
    url: str | Missing


class EmbedImage(ObjDict):
    url: str
    proxy_url: str | Missing
    height: int | Missing
    width: int | Missing


class EmbedVideo(ObjDict):
    url: str | Missing
    proxy_url: str | Missing
    height: int | Missing
    width: int | Missing


class EmbedThumbnail(ObjDict):
    url: str
    proxy_url: str | Missing
    height: int | Missing
    width: int | Missing


class Embed(ObjDict):
    title: str | Missing
    type: str | Missing
    description: str | Missing
    url: str | Missing
    timestamp: ISOTimestamp | Missing
    color: int | Missing
    footer: EmbedFooter | Missing
    image: EmbedImage | Missing
    thumbnail: EmbedThumbnail | Missing
    video: EmbedVideo | Missing
    provider: EmbedProvider | Missing
    author: EmbedAuthor | Missing
    fields: list[EmbedField] | Missing
