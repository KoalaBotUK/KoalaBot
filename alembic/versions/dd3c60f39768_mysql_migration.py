"""mysql migration

Revision ID: dd3c60f39768
Revises: 
Create Date: 2022-02-23 18:54:15.064055

"""
import logging
import os
from enum import Enum
from pathlib import Path
from sqlite3 import OperationalError

import discord
import sqlalchemy.dialects.mysql.base
from alembic import op
from discord import ActivityType
from sqlalchemy import Column, String, VARCHAR, INT, FLOAT, BOOLEAN, ForeignKey, TIMESTAMP, types
from sqlalchemy.exc import IntegrityError as SaIntegrityError
from pymysql.err import IntegrityError as PmyIntegrityError


# Config Path
CONFIG_PATH = os.environ.get("CONFIG_PATH")

if not CONFIG_PATH:
    CONFIG_PATH = "/config"
    if os.name == 'nt':
        CONFIG_PATH = '.'+CONFIG_PATH
CONFIG_PATH = Path(CONFIG_PATH)
CONFIG_PATH.mkdir(exist_ok=True, parents=True)

# Use SQLite
ENCRYPTED_DB = (not os.name == 'nt') and eval(os.environ.get('ENCRYPTED', "True"))

if ENCRYPTED_DB:
    print(f"ENCRYPTED_DB{ENCRYPTED_DB}")
if os.name == 'nt' or not ENCRYPTED_DB:
    print("Database Encryption Disabled")
    import sqlite3
else:
    print("Database Encryption Enabled")
    from pysqlcipher3 import dbapi2 as sqlite3

SQLITE_DB_KEY = os.environ.get('SQLITE_KEY', "2DD29CA851E7B56E4697B0E1F08507293D761A05CE4D1B628663F411A8086D99")
SQLITE_DB_PATH = Path(CONFIG_PATH, "Koala.db" if ENCRYPTED_DB else "windows_Koala.db")
SQLITE_DB_PATH.touch()
if ENCRYPTED_DB:
    os.system(f"chown www-data {CONFIG_PATH.absolute()}")
    os.system(f"chmod 777 {CONFIG_PATH}")


def insert_ignore_duplicates(table, data):
    bulk_amount = 100
    for i in range(0, len(data), bulk_amount):
        data_chunk = data[i:i + bulk_amount]
        print(f"insterting {i}")
        try:
            op.bulk_insert(table, data_chunk)
        except (SaIntegrityError, PmyIntegrityError):
            for item in data_chunk:
                try:
                    op.bulk_insert(table, [item])
                except (SaIntegrityError, PmyIntegrityError) as err2:
                    # ignore integrity errors
                    print(err2)
                except TypeError as tpe:
                    print(f"ERROR: {item}")
                    raise tpe


# revision identifiers, used by Alembic.
revision = 'dd3c60f39768'
down_revision = None
branch_labels = None
depends_on = None


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class DiscordActivityType(types.TypeDecorator):
    """
    Uses ActivityType for python, but TINYINT(2) for storing in db
    """

    impl = sqlalchemy.dialects.mysql.TINYINT(2)

    cache_ok = True

    def process_bind_param(self, value, dialect):
        return discord.ActivityType[value].value if value else None

    def process_literal_param(self, value, dialect):
        return discord.ActivityType[value].value if value else None

    def process_result_value(self, value, dialect):
        return ActivityType(value) if value else None

    def copy(self, **kw):
        return DiscordActivityType()

    @property
    def python_type(self):
        return ActivityType

class DiscordSnowflake(types.TypeDecorator):
    """
    Uses int for python, but DiscordSnowflake for storing in db
    """

    impl = types.VARCHAR(20)

    cache_ok = True

    def process_bind_param(self, value, dialect):
        return str(value) if value else None

    def process_literal_param(self, value, dialect):
        return str(value) if value else None

    def process_result_value(self, value, dialect):
        return int(value) if value else None

    def copy(self, **kw):
        return DiscordSnowflake(self.impl.length)

    @property
    def python_type(self):
        return int


def upgrade():
    try:
        unsafe_upgrade()
    except Exception as e:
        downgrade(exception=e)


def unsafe_upgrade():
    guilds = op.create_table("Guilds",
                             Column('guild_id', DiscordSnowflake, primary_key=True),
                             Column('subscription', INT, server_default='0'))
    koala_extensions = op.create_table("KoalaExtensions",
                                       Column('extension_id', VARCHAR(20), primary_key=True),
                                       Column('subscription_required', INT, server_default='0'),
                                       Column('available', BOOLEAN, server_default='1'),
                                       Column('enabled', BOOLEAN, server_default='1'))
    guild_extensions = op.create_table('GuildExtensions',
                                       Column('extension_id', VARCHAR(20),
                                              ForeignKey("KoalaExtensions.extension_id", ondelete='CASCADE'), primary_key=True),
                                       Column('guild_id', DiscordSnowflake, primary_key=True))

    scheduled_activities = op.create_table('ScheduledActivities',
                                           Column('activity_id', INT, primary_key=True, autoincrement=True),
                                           Column('activity_type', DiscordActivityType,
                                                  comment="-1: unknown, 0: Playing, 1: Streaming, 2: Listening, "
                                                          "3: Watching, 4: Custom, 5: Competing"),
                                           Column('stream_url', VARCHAR(100), nullable=True),
                                           Column('message', VARCHAR(100)),
                                           Column('time_start', TIMESTAMP),
                                           Column('time_end', TIMESTAMP))
    guild_usage = op.create_table('GuildUsage',
                                  Column('guild_id', DiscordSnowflake, ForeignKey("Guilds.guild_id", ondelete='CASCADE'), primary_key=True),
                                  Column('last_message_epoch_time', INT))
    guild_colour_change_permissions = op.create_table('GuildColourChangePermissions',
                                                      Column('guild_id', DiscordSnowflake,
                                                             ForeignKey("Guilds.guild_id", ondelete='CASCADE'), primary_key=True),
                                                      Column('role_id', DiscordSnowflake, primary_key=True))
    guild_invalid_custom_colour_roles = op.create_table('GuildInvalidCustomColourRoles',
                                                        Column('guild_id', DiscordSnowflake,
                                                               ForeignKey("Guilds.guild_id", ondelete='CASCADE'),
                                                               primary_key=True),
                                                        Column('role_id', DiscordSnowflake, primary_key=True))

    guild_welcome_messages = op.create_table('GuildWelcomeMessages',
                                             Column('guild_id', DiscordSnowflake, primary_key=True),
                                             Column('welcome_message', String(2000, collation="utf8mb4_general_ci"), nullable=True))

    guild_rfr_messages = op.create_table('GuildRFRMessages',
                                         Column('guild_id', DiscordSnowflake, ForeignKey("Guilds.guild_id", ondelete='CASCADE')),
                                         Column('channel_id', DiscordSnowflake),
                                         Column('message_id', DiscordSnowflake),
                                         Column('emoji_role_id', INT, primary_key=True))
    op.create_unique_constraint('uniq_message', 'GuildRFRMessages', ['guild_id', 'channel_id', 'message_id'])
    rfr_message_emoji_roles = op.create_table('RFRMessageEmojiRoles',
                                              Column('emoji_role_id', INT,
                                                     ForeignKey("GuildRFRMessages.emoji_role_id", ondelete='CASCADE'), primary_key=True),
                                              Column('emoji_raw', VARCHAR(50, collation="utf8mb4_general_ci"), primary_key=True),
                                              Column('role_id', DiscordSnowflake, primary_key=True))
    op.create_unique_constraint('uniq_emoji', 'RFRMessageEmojiRoles', ['emoji_role_id', 'emoji_raw'])
    op.create_unique_constraint('uniq_role_emoji', 'RFRMessageEmojiRoles', ['emoji_role_id', 'role_id'])
    guild_rfr_required_roles = op.create_table('GuildRFRRequiredRoles',
                                               Column('guild_id', DiscordSnowflake,
                                                      ForeignKey("Guilds.guild_id", ondelete='CASCADE'), primary_key=True),
                                               Column('role_id', DiscordSnowflake, primary_key=True))
    op.create_unique_constraint('uniq_guild_role', 'GuildRFRRequiredRoles', ['guild_id', 'role_id'])

    text_filter = op.create_table('TextFilter',
                                  Column('filtered_text_id', String(100, collation="utf8mb4_general_ci"), primary_key=True),
                                  Column('guild_id', DiscordSnowflake),
                                  Column('filtered_text', VARCHAR(100, collation="utf8mb4_general_ci")),
                                  Column('filter_type', VARCHAR(10)),
                                  Column('is_regex', BOOLEAN))
    text_filter_moderation = op.create_table('TextFilterModeration',
                                             Column('channel_id', DiscordSnowflake, primary_key=True),
                                             Column('guild_id', DiscordSnowflake))
    text_filter_ignore_list = op.create_table('TextFilterIgnoreList',
                                              Column('ignore_id', VARCHAR(36), primary_key=True),
                                              Column('guild_id', DiscordSnowflake),
                                              Column('ignore_type', VARCHAR(10)),
                                              Column('ignore', DiscordSnowflake))

    twitch_alerts = op.create_table('TwitchAlerts',
                                    Column('guild_id', DiscordSnowflake,
                                           ForeignKey("Guilds.guild_id", ondelete='CASCADE')),
                                    Column('channel_id', DiscordSnowflake, primary_key=True),
                                    Column('default_message', VARCHAR(1000, collation="utf8mb4_general_ci")))
    user_in_twitch_alert = op.create_table('UserInTwitchAlert',
                                           Column('channel_id', DiscordSnowflake,
                                                  ForeignKey("TwitchAlerts.channel_id", ondelete='CASCADE'), primary_key=True),
                                           Column('twitch_username', VARCHAR(25), primary_key=True),
                                           Column('custom_message', VARCHAR(1000, collation="utf8mb4_general_ci"), nullable=True),
                                           Column('message_id', DiscordSnowflake, nullable=True))
    team_in_twitch_alert = op.create_table('TeamInTwitchAlert',
                                           Column('team_twitch_alert_id', INT,
                                                  autoincrement=True, primary_key=True),
                                           Column('channel_id', DiscordSnowflake, ForeignKey("TwitchAlerts.channel_id", ondelete='CASCADE')),
                                           Column('twitch_team_name', VARCHAR(25)),
                                           Column('custom_message', VARCHAR(1000, collation="utf8mb4_general_ci"), nullable=True))
    user_in_twitch_team = op.create_table('UserInTwitchTeam',
                                          Column('team_twitch_alert_id', INT,
                                                 ForeignKey("TeamInTwitchAlert.team_twitch_alert_id", ondelete='CASCADE'),
                                                 primary_key=True),
                                          Column('twitch_username', VARCHAR(25), primary_key=True),
                                          Column('message_id', DiscordSnowflake, nullable=True))

    verified_emails = op.create_table('verified_emails',
                                      Column('u_id', DiscordSnowflake, primary_key=True),
                                      Column('email', VARCHAR(100, collation="utf8_bin"), primary_key=True))
    non_verified_emails = op.create_table('non_verified_emails',
                                          Column('u_id', DiscordSnowflake),
                                          Column('email', VARCHAR(100)),
                                          Column('token', VARCHAR(8), primary_key=True))
    roles = op.create_table('roles',
                            Column('s_id', DiscordSnowflake, ForeignKey("Guilds.guild_id", ondelete='CASCADE'), primary_key=True),
                            Column('r_id', DiscordSnowflake, primary_key=True),
                            Column('email_suffix', VARCHAR(100), primary_key=True))
    to_re_verify = op.create_table('to_re_verify',
                                   Column('u_id', DiscordSnowflake, primary_key=True),
                                   Column('r_id', DiscordSnowflake, primary_key=True))
    verify_blacklist = op.create_table('VerifyBlacklist',
                                   Column('user_id', DiscordSnowflake, primary_key=True),
                                   Column('role_id', DiscordSnowflake, primary_key=True),
                                   Column('email_suffix', DiscordSnowflake, primary_key=True))


    votes = op.create_table('Votes',
                            Column('vote_id', DiscordSnowflake, primary_key=True),
                            Column('author_id', DiscordSnowflake),
                            Column('guild_id', DiscordSnowflake),
                            Column('title', VARCHAR(200, collation="utf8mb4_general_ci")),
                            Column('chair_id', DiscordSnowflake, nullable=True),
                            Column('voice_id', DiscordSnowflake, nullable=True),
                            Column('end_time', FLOAT, nullable=True))
    vote_target_roles = op.create_table('VoteTargetRoles',
                                        Column('vote_id', DiscordSnowflake, primary_key=True),
                                        Column('role_id', DiscordSnowflake, primary_key=True))
    vote_options = op.create_table('VoteOptions',
                                   Column('vote_id', DiscordSnowflake, primary_key=True),
                                   Column('opt_id', DiscordSnowflake, primary_key=True),
                                   Column('option_title', VARCHAR(150, collation="utf8mb4_general_ci")),
                                   Column('option_desc', VARCHAR(150, collation="utf8mb4_general_ci")))
    vote_sent = op.create_table('VoteSent',
                                Column('vote_id', DiscordSnowflake, primary_key=True),
                                Column('vote_receiver_id', DiscordSnowflake, primary_key=True),
                                Column('vote_receiver_message', DiscordSnowflake))

    # Copy data to new db
    conn = sqlite3.connect(str(SQLITE_DB_PATH.absolute()))
    conn.row_factory = dict_factory
    c = conn.cursor()
    if not (os.name == 'nt' or not ENCRYPTED_DB):
        c.execute('''PRAGMA key="x'{}'"'''.format(SQLITE_DB_KEY))

    # koala
    try:
        c.execute("SELECT DISTINCT guild_id FROM GuildExtensions")
    except OperationalError:
        logging.warning("Query error for old database, assuming no prior setup, insert will stop")
        return
    op.bulk_insert(guilds, c.fetchall())

    c.execute("SELECT * FROM KoalaExtensions")
    op.bulk_insert(koala_extensions, c.fetchall())

    c.execute("SELECT * FROM GuildExtensions")
    op.bulk_insert(guild_extensions, c.fetchall())

    # base
    c.execute("SELECT * FROM ScheduledActivities")
    op.bulk_insert(scheduled_activities, c.fetchall())

    # announce
    c.execute("SELECT * FROM GuildUsage")
    op.bulk_insert(guild_usage, c.fetchall())

    # colour role
    c.execute("SELECT * FROM GuildColourChangePermissions")
    op.bulk_insert(guild_colour_change_permissions, c.fetchall())

    c.execute("SELECT * FROM GuildInvalidCustomColourRoles")
    op.bulk_insert(guild_invalid_custom_colour_roles, c.fetchall())

    # intro cog
    c.execute("SELECT * FROM GuildWelcomeMessages")
    op.bulk_insert(guild_welcome_messages, c.fetchall())

    # react for role
    c.execute("SELECT * FROM GuildRFRMessages")
    op.bulk_insert(guild_rfr_messages, c.fetchall())

    c.execute("SELECT * FROM RFRMessageEmojiRoles")
    op.bulk_insert(rfr_message_emoji_roles, c.fetchall())

    c.execute("SELECT * FROM GuildRFRRequiredRoles")
    op.bulk_insert(guild_rfr_required_roles, c.fetchall())

    # text filter
    c.execute("SELECT * FROM TextFilter")
    op.bulk_insert(text_filter, c.fetchall())

    c.execute("SELECT * FROM TextFilterModeration")
    op.bulk_insert(text_filter_moderation, c.fetchall())

    c.execute("SELECT * FROM TextFilterIgnoreList")
    op.bulk_insert(text_filter_ignore_list, c.fetchall())

    # twitch alert
    c.execute("SELECT * FROM TwitchAlerts")
    op.bulk_insert(twitch_alerts, c.fetchall())

    c.execute("SELECT * FROM UserInTwitchAlert")
    op.bulk_insert(user_in_twitch_alert, c.fetchall())

    c.execute("SELECT * FROM TeamInTwitchAlert")
    op.bulk_insert(team_in_twitch_alert, c.fetchall())

    c.execute("SELECT * FROM UserInTwitchTeam")
    op.bulk_insert(user_in_twitch_team, c.fetchall())

    # verification
    c.execute("SELECT * FROM verified_emails ORDER BY email")
    insert_ignore_duplicates(verified_emails, c.fetchall())

    c.execute("SELECT * FROM non_verified_emails")
    op.bulk_insert(non_verified_emails, c.fetchall())

    c.execute("SELECT * FROM roles")
    insert_ignore_duplicates(roles, c.fetchall())

    c.execute("SELECT * FROM to_re_verify")
    op.bulk_insert(to_re_verify, c.fetchall())

    c.execute("SELECT * FROM VerifyBlacklist")
    op.bulk_insert(verify_blacklist, c.fetchall())

    # voting
    c.execute("SELECT * FROM Votes")
    op.bulk_insert(votes, c.fetchall())

    c.execute("SELECT * FROM VoteTargetRoles")
    op.bulk_insert(vote_target_roles, c.fetchall())

    c.execute("SELECT * FROM VoteOptions")
    op.bulk_insert(vote_options, c.fetchall())

    c.execute("SELECT * FROM VoteSent")
    op.bulk_insert(vote_sent, c.fetchall())

    c.close()
    conn.close()


def downgrade(exception=None):
    tables = ["VoteSent", "VoteOptions", "VoteTargetRoles", "Votes",
              "VerifyBlacklist", "to_re_verify", "non_verified_emails", "verified_emails", "roles",
              "UserInTwitchTeam", "TeamInTwitchAlert", "UserInTwitchAlert", "TwitchAlerts",
              "TextFilterIgnoreList", "TextFilterModeration", "TextFilter",
              "GuildRFRRequiredRoles", "RFRMessageEmojiRoles", "GuildRFRMessages",
              "GuildWelcomeMessages",
              "GuildUsage",
              "GuildInvalidCustomColourRoles", "GuildColourChangePermissions",
              "ScheduledActivities",
              "GuildExtensions", "KoalaExtensions", "Guilds"]

    for table in tables:
        try:
            op.drop_table(table)
        except Exception:
            continue

    if exception:
        raise exception