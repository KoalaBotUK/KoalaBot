from sqlalchemy import Column, VARCHAR, BOOLEAN

from koala.models import mapper_registry, DiscordSnowflake


@mapper_registry.mapped
class TextFilter:
    __tablename__ = 'TextFilter'
    filtered_text_id = Column(VARCHAR(100, collation="utf8mb4_unicode_520_ci"), primary_key=True)
    guild_id = Column(DiscordSnowflake)
    filtered_text = Column(VARCHAR(100, collation="utf8mb4_unicode_520_ci"))
    filter_type = Column(VARCHAR(10))
    is_regex = Column(BOOLEAN)

    def __repr__(self):
        return "<TextFilter(%s, %s, %s, %s, %s)>" % \
               (self.filtered_text_id, self.guild_id, self.filtered_text, self.filter_type, self.is_regex)


@mapper_registry.mapped
class TextFilterModeration:
    __tablename__ = 'TextFilterModeration'
    channel_id = Column(DiscordSnowflake, primary_key=True)
    guild_id = Column(DiscordSnowflake)

    def __repr__(self):
        return "<TextFilterModeration(%s, %s)>" % \
               (self.channel_id, self.guild_id)


@mapper_registry.mapped
class TextFilterIgnoreList:
    __tablename__ = 'TextFilterIgnoreList'
    ignore_id = Column(VARCHAR(40), primary_key=True)
    guild_id = Column(DiscordSnowflake)
    ignore_type = Column(VARCHAR(10))
    ignore = Column(DiscordSnowflake)

    def __repr__(self):
        return "<TextFilterIgnoreList(%s, %s, %s, %s)>" % \
               (self.ignore_id, self.guild_id, self.ignore_type, self.ignore)
