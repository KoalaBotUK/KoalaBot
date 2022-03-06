from sqlalchemy import Column, INT, VARCHAR, ForeignKey, orm
from koala.models import mapper_registry, DiscordSnowflake


@mapper_registry.mapped
class TwitchAlerts:
    __tablename__ = 'TwitchAlerts'
    guild_id = Column(DiscordSnowflake, ForeignKey("Guilds.guild_id"))
    channel_id = Column(DiscordSnowflake, primary_key=True)
    default_message = Column(VARCHAR(1000, collation="utf8mb4_general_ci"))

    def __repr__(self):
        return "<TwitchAlerts(%s, %s, %s)>" % \
               (self.guild_id, self.channel_id, self.default_message)


@mapper_registry.mapped
class UserInTwitchAlert:
    __tablename__ = 'UserInTwitchAlert'
    channel_id = Column(DiscordSnowflake, ForeignKey("TwitchAlerts.channel_id"), primary_key=True)
    twitch_username = Column(VARCHAR(25), primary_key=True)
    custom_message = Column(VARCHAR(1000, collation="utf8mb4_general_ci"), nullable=True)
    message_id = Column(DiscordSnowflake, nullable=True)
    twitch_alert = orm.relationship("TwitchAlerts")

    def __repr__(self):
        return "<UserInTwitchAlert(%s, %s, %s, %s)>" % \
               (self.channel_id, self.twitch_username, self.custom_message, self.message_id)


@mapper_registry.mapped
class TeamInTwitchAlert:
    __tablename__ = 'TeamInTwitchAlert'
    team_twitch_alert_id = Column(INT, autoincrement=True, primary_key=True)
    channel_id = Column(DiscordSnowflake, ForeignKey("TwitchAlerts.channel_id"))
    twitch_team_name = Column(VARCHAR(25))
    custom_message = Column(VARCHAR(1000, collation="utf8mb4_general_ci"), nullable=True)
    twitch_alert = orm.relationship("TwitchAlerts")

    def __repr__(self):
        return "<TeamInTwitchAlert(%s, %s, %s, %s)>" % \
               (self.team_twitch_alert_id, self.channel_id, self.twitch_team_name, self.custom_message)


@mapper_registry.mapped
class UserInTwitchTeam:
    __tablename__ = 'UserInTwitchTeam'
    team_twitch_alert_id = Column(INT, ForeignKey("TeamInTwitchAlert.team_twitch_alert_id"), primary_key=True)
    twitch_username = Column(VARCHAR(25), primary_key=True)
    message_id = Column(DiscordSnowflake, nullable=True)
    team = orm.relationship("TeamInTwitchAlert")

    def __repr__(self):
        return "<UserInTwitchTeam(%s, %s, %s)>" % \
               (self.team_twitch_alert_id, self.twitch_username, self.message_id)
