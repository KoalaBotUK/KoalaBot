"""KB2 extensions

Revision ID: 51ccdeec4499
Revises: dd3c60f39768
Create Date: 2024-10-12 17:21:58.692393

"""
import os

from alembic import op
import sqlalchemy as sa
from pynamodb.attributes import MapAttribute, UnicodeAttribute, DiscriminatorAttribute, NumberAttribute, \
    BooleanAttribute, DynamicMapAttribute, ListAttribute
from pynamodb.models import Model

# revision identifiers, used by Alembic.
revision = '51ccdeec4499'
down_revision = 'dd3c60f39768'
branch_labels = None
depends_on = None

ENV_PREFIX = os.environ.get("ENV_PREFIX", "")


class ExtensionAttr(MapAttribute):
    cls = DiscriminatorAttribute()
    id: str = UnicodeAttribute(hash_key=True)
    name: str = UnicodeAttribute()
    emoji: str = UnicodeAttribute()
    version: int = NumberAttribute(default=1)
    enabled: bool = BooleanAttribute()
    hidden: bool = BooleanAttribute()
    data: dict = DynamicMapAttribute()


class LegacyExtension(ExtensionAttr, discriminator="legacy"):
    pass


class Guild(Model):
    class Meta:
        table_name = f'{ENV_PREFIX}kb_guilds'
        region = 'eu-west-2'

    guild_id: str = UnicodeAttribute(hash_key=True)
    extensions: list[ExtensionAttr] = ListAttribute(of=ExtensionAttr, default=list)


DEFAULT_LEGACY_EXTENSIONS = [
    LegacyExtension(id="announce", name="Announce", emoji="📢", version=1, enabled=False, hidden=False, data={}),
    LegacyExtension(id="colour_role", name="Colour Role", emoji="🎨", version=1, enabled=False, hidden=False, data={}),
    LegacyExtension(id="rfr", name="React for Role", emoji="👍", version=1, enabled=False, hidden=False, data={}),
    LegacyExtension(id="filter", name="Text Filter", emoji="🔎", version=1, enabled=False, hidden=False, data={}),
    LegacyExtension(id="twitch_alert", name="Twitch Alert", emoji="🔔", version=1, enabled=False, hidden=False, data={}),
    LegacyExtension(id="verify", name="Verify", emoji="✅", version=1, enabled=False, hidden=False, data={}),
    LegacyExtension(id="vote", name="Vote", emoji="🗳", version=1, enabled=False, hidden=False, data={})
]

map_ext = {
    "Announce": "announce",
    "ColourRole": "colour_role",
    "ReactForRole": "rfr",
    "TextFilter": "filter",
    "TwitchAlert": "twitch_alert",
    "Verify": "verify",
    "Vote": "vote"
}


def upgrade():
    conn = op.get_bind()
    rs = conn.execute("SELECT guild_id, extension_id FROM GuildExtensions")
    rs = rs.fetchall()
    Guild(guild_id="DEFAULT", extensions=DEFAULT_LEGACY_EXTENSIONS).save()
    exts = {}
    for guild_id, extension_id in rs:
        guild_exts = exts.get(guild_id, DEFAULT_LEGACY_EXTENSIONS)
        for guild_ext in guild_exts:
            if guild_ext.id == map_ext[extension_id]:
                guild_ext.enabled = True
        exts[guild_id] = guild_exts

    for guild_id in exts:
        Guild(guild_id=guild_id, extensions=exts[guild_id]).save()


def downgrade():
    rs = Guild.scan()
    for guild in rs:
        guild.delete()
