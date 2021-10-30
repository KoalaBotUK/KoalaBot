from sqlalchemy import Column, Integer, String, ForeignKey, orm
from koala.models import Base


class TwitchAlerts(Base):
    __tablename__ = 'TwitchAlerts'
    guild_id = Column(Integer, ForeignKey("GuildExtensions.guild_id"), primary_key=True)
    channel_id = Column(Integer, primary_key=True)
    default_message = Column(String)


class UserInTwitchAlert(Base):
    __tablename__ = 'UserInTwitchAlert'
    channel_id = Column(Integer, ForeignKey("TwitchAlerts.channel_id"), primary_key=True)
    twitch_username = Column(String, primary_key=True)
    custom_message = Column(String, nullable=True)
    message_id = Column(Integer, nullable=True)
    twitch_alert = orm.relationship("TwitchAlerts")


class TeamInTwitchAlert(Base):
    __tablename__ = 'TeamInTwitchAlert'
    team_twitch_alert_id = Column(Integer, autoincrement=True, primary_key=True)
    channel_id = Column(Integer, ForeignKey("TwitchAlerts.channel_id"))
    twitch_team_name = Column(String)
    custom_message = Column(String, nullable=True)
    twitch_alert = orm.relationship("TwitchAlerts")


class UserInTwitchTeam(Base):
    __tablename__ = 'UserInTwitchTeam'
    team_twitch_alert_id = Column(Integer, ForeignKey("TeamInTwitchAlert.team_twitch_alert_id"), primary_key=True)
    twitch_username = Column(String, primary_key=True)
    message_id = Column(Integer, nullable=True)
    team = orm.relationship("TeamInTwitchAlert")
