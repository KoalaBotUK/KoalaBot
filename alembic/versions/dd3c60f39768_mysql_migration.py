"""mysql migration

Revision ID: dd3c60f39768
Revises: 
Create Date: 2022-02-23 18:54:15.064055

"""
import os
from pathlib import Path

from alembic import op
from sqlalchemy import Column, String, VARCHAR, INT, FLOAT, BOOLEAN, ForeignKey
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


def upgrade():
    guilds = op.create_table("Guilds",
                             Column('guild_id', VARCHAR(18), primary_key=True),
                             Column('subscription', INT, server_default='0'))
    koala_extensions = op.create_table("KoalaExtensions",
                                       Column('extension_id', VARCHAR(20), primary_key=True),
                                       Column('subscription_required', INT, server_default='0'),
                                       Column('available', BOOLEAN, server_default='1'),
                                       Column('enabled', BOOLEAN, server_default='1'))
    guild_extensions = op.create_table('GuildExtensions',
                                       Column('extension_id', VARCHAR(20),
                                              ForeignKey("KoalaExtensions.extension_id"), primary_key=True),
                                       Column('guild_id', VARCHAR(18), primary_key=True))

    guild_usage = op.create_table('GuildUsage',
                                  Column('guild_id', VARCHAR(18), ForeignKey("Guilds.guild_id"), primary_key=True),
                                  Column('last_message_epoch_time', INT))

    guild_colour_change_permissions = op.create_table('GuildColourChangePermissions',
                                                      Column('guild_id', VARCHAR(18),
                                                             ForeignKey("Guilds.guild_id"), primary_key=True),
                                                      Column('role_id', VARCHAR(18), primary_key=True))
    guild_invalid_custom_colour_roles = op.create_table('GuildInvalidCustomColourRoles',
                                                        Column('guild_id', VARCHAR(18),
                                                               ForeignKey("Guilds.guild_id"),
                                                               primary_key=True),
                                                        Column('role_id', VARCHAR(18), primary_key=True))

    guild_welcome_messages = op.create_table('GuildWelcomeMessages',
                                             Column('guild_id', VARCHAR(18), primary_key=True),
                                             Column('welcome_message', String(2000, collation="utf8mb4_general_ci"), nullable=True))

    guild_rfr_messages = op.create_table('GuildRFRMessages',
                                         Column('guild_id', VARCHAR(18), ForeignKey("Guilds.guild_id")),
                                         Column('channel_id', VARCHAR(18)),
                                         Column('message_id', VARCHAR(18)),
                                         Column('emoji_role_id', INT, primary_key=True))
    op.create_unique_constraint('uniq_message', 'GuildRFRMessages', ['guild_id', 'channel_id', 'message_id'])
    rfr_message_emoji_roles = op.create_table('RFRMessageEmojiRoles',
                                              Column('emoji_role_id', INT,
                                                     ForeignKey("GuildRFRMessages.emoji_role_id"), primary_key=True),
                                              Column('emoji_raw', VARCHAR(50, collation="utf8mb4_general_ci"), primary_key=True),
                                              Column('role_id', VARCHAR(18), primary_key=True))
    op.create_unique_constraint('uniq_emoji', 'RFRMessageEmojiRoles', ['emoji_role_id', 'emoji_raw'])
    op.create_unique_constraint('uniq_role_emoji', 'RFRMessageEmojiRoles', ['emoji_role_id', 'role_id'])
    guild_rfr_required_roles = op.create_table('GuildRFRRequiredRoles',
                                               Column('guild_id', VARCHAR(18),
                                                      ForeignKey("Guilds.guild_id"), primary_key=True),
                                               Column('role_id', VARCHAR(18), primary_key=True))
    op.create_unique_constraint('uniq_guild_role', 'GuildRFRRequiredRoles', ['guild_id', 'role_id'])

    text_filter = op.create_table('TextFilter',
                                  Column('filtered_text_id', String(100, collation="utf8mb4_general_ci"), primary_key=True),
                                  Column('guild_id', VARCHAR(18)),
                                  Column('filtered_text', VARCHAR(100, collation="utf8mb4_general_ci")),
                                  Column('filter_type', VARCHAR(10)),
                                  Column('is_regex', BOOLEAN))
    text_filter_moderation = op.create_table('TextFilterModeration',
                                             Column('channel_id', VARCHAR(18), primary_key=True),
                                             Column('guild_id', VARCHAR(18)))
    text_filter_ignore_list = op.create_table('TextFilterIgnoreList',
                                              Column('ignore_id', VARCHAR(36), primary_key=True),
                                              Column('guild_id', VARCHAR(18)),
                                              Column('ignore_type', VARCHAR(10)),
                                              Column('ignore', VARCHAR(18)))

    twitch_alerts = op.create_table('TwitchAlerts',
                                    Column('guild_id', VARCHAR(18),
                                           ForeignKey("Guilds.guild_id")),
                                    Column('channel_id', VARCHAR(18), primary_key=True),
                                    Column('default_message', VARCHAR(1000, collation="utf8mb4_general_ci")))
    user_in_twitch_alert = op.create_table('UserInTwitchAlert',
                                           Column('channel_id', VARCHAR(18),
                                                  ForeignKey("TwitchAlerts.channel_id"), primary_key=True),
                                           Column('twitch_username', VARCHAR(25), primary_key=True),
                                           Column('custom_message', VARCHAR(1000, collation="utf8mb4_general_ci"), nullable=True),
                                           Column('message_id', VARCHAR(18), nullable=True))
    team_in_twitch_alert = op.create_table('TeamInTwitchAlert',
                                           Column('team_twitch_alert_id', INT,
                                                  autoincrement=True, primary_key=True),
                                           Column('channel_id', VARCHAR(18), ForeignKey("TwitchAlerts.channel_id")),
                                           Column('twitch_team_name', VARCHAR(25)),
                                           Column('custom_message', VARCHAR(1000, collation="utf8mb4_general_ci"), nullable=True))
    user_in_twitch_team = op.create_table('UserInTwitchTeam',
                                          Column('team_twitch_alert_id', INT,
                                                 ForeignKey("TeamInTwitchAlert.team_twitch_alert_id"),
                                                 primary_key=True),
                                          Column('twitch_username', VARCHAR(25), primary_key=True),
                                          Column('message_id', VARCHAR(18), nullable=True))

    verified_emails = op.create_table('verified_emails',
                                      Column('u_id', VARCHAR(18), primary_key=True),
                                      Column('email', VARCHAR(100, collation="utf8_bin"), primary_key=True))
    non_verified_emails = op.create_table('non_verified_emails',
                                          Column('u_id', VARCHAR(18)),
                                          Column('email', VARCHAR(100)),
                                          Column('token', VARCHAR(8), primary_key=True))
    roles = op.create_table('roles',
                            Column('s_id', VARCHAR(18), ForeignKey("Guilds.guild_id"), primary_key=True),
                            Column('r_id', VARCHAR(18), primary_key=True),
                            Column('email_suffix', VARCHAR(100), primary_key=True))
    to_re_verify = op.create_table('to_re_verify',
                                   Column('u_id', VARCHAR(18), primary_key=True),
                                   Column('r_id', VARCHAR(18), primary_key=True))

    votes = op.create_table('Votes',
                            Column('vote_id', VARCHAR(18), primary_key=True),
                            Column('author_id', VARCHAR(18)),
                            Column('guild_id', VARCHAR(18)),
                            Column('title', VARCHAR(200, collation="utf8mb4_general_ci")),
                            Column('chair_id', VARCHAR(18), nullable=True),
                            Column('voice_id', VARCHAR(18), nullable=True),
                            Column('end_time', FLOAT, nullable=True))
    vote_target_roles = op.create_table('VoteTargetRoles',
                                        Column('vote_id', VARCHAR(18), primary_key=True),
                                        Column('role_id', VARCHAR(18), primary_key=True))
    vote_options = op.create_table('VoteOptions',
                                   Column('vote_id', VARCHAR(18), primary_key=True),
                                   Column('opt_id', VARCHAR(18), primary_key=True),
                                   Column('option_title', VARCHAR(150, collation="utf8mb4_general_ci")),
                                   Column('option_desc', VARCHAR(150, collation="utf8mb4_general_ci")))
    vote_sent = op.create_table('VoteSent',
                                Column('vote_id', VARCHAR(18), primary_key=True),
                                Column('vote_receiver_id', VARCHAR(18), primary_key=True),
                                Column('vote_receiver_message', VARCHAR(18)))

    # Copy data to new db
    conn = sqlite3.connect(str(SQLITE_DB_PATH.absolute()))
    conn.row_factory = dict_factory
    c = conn.cursor()
    if not (os.name == 'nt' or not ENCRYPTED_DB):
        c.execute('''PRAGMA key="x'{}'"'''.format(SQLITE_DB_KEY))

    # koala

    c.execute("SELECT DISTINCT guild_id FROM GuildExtensions")
    op.bulk_insert(guilds, c.fetchall())

    c.execute("SELECT * FROM KoalaExtensions")
    op.bulk_insert(koala_extensions, c.fetchall())

    c.execute("SELECT * FROM GuildExtensions")
    op.bulk_insert(guild_extensions, c.fetchall())

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


def downgrade():
    op.drop_table("VoteSent")
    op.drop_table("VoteOptions")
    op.drop_table("VoteTargetRoles")
    op.drop_table("Votes")

    op.drop_table("to_re_verify")
    op.drop_table("non_verified_emails")
    op.drop_table("verified_emails")
    op.drop_table("roles")

    op.drop_table("UserInTwitchTeam")
    op.drop_table("TeamInTwitchAlert")
    op.drop_table("UserInTwitchAlert")
    op.drop_table("TwitchAlerts")

    op.drop_table("TextFilterIgnoreList")
    op.drop_table("TextFilterModeration")
    op.drop_table("TextFilter")

    op.drop_table("GuildRFRRequiredRoles")
    op.drop_table("RFRMessageEmojiRoles")
    op.drop_table("GuildRFRMessages")

    op.drop_table("GuildWelcomeMessages")

    op.drop_table("GuildUsage")

    op.drop_table("GuildInvalidCustomColourRoles")
    op.drop_table("GuildColourChangePermissions")

    op.drop_table("GuildExtensions")
    op.drop_table("KoalaExtensions")
    op.drop_table("Guilds")

