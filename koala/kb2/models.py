from typing import List

from pynamodb.attributes import NumberAttribute, BooleanAttribute, UnicodeAttribute, MapAttribute, ListAttribute
from pynamodb.models import Model

from koala import env

error_versions = {}

class ExtensionAttr(MapAttribute):
    id: str = UnicodeAttribute(hash_key=True)
    version: int = NumberAttribute()
    enabled: bool = BooleanAttribute()


class Guild(Model):
    class Meta:
        table_name = f'{env.ENV_PREFIX}kb_guilds'
        region = 'eu-west-2'

    guild_id: str = UnicodeAttribute(hash_key=True)
    extensions: List[ExtensionAttr] = ListAttribute(of=ExtensionAttr, default=list)


map_ext = {
    "Announce": "announce",
    "ColourRole": "colour_role",
    "ReactForRole": "rfr",
    "TextFilter": "filter",
    "TwitchAlert": "twitch_alert",
    "Verify": "verify",
    "Vote": "vote"
}

