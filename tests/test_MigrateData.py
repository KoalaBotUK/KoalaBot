import os
import pathlib
import random

# Libs
from dotenv import load_dotenv

load_dotenv()
ENCRYPTED_DB = eval(os.environ.get('ENCRYPTED', "True"))
if ENCRYPTED_DB:
    print(f"ENCRYPTED_DB{ENCRYPTED_DB}")
if os.name == 'nt' or not ENCRYPTED_DB:
    print("Database Encryption Disabled")
    import sqlite3
else:
    print("Database Encryption Enabled")
    from pysqlcipher3 import dbapi2 as sqlite3

import pytest

import KoalaBot
from utils.KoalaDBManager import KoalaDBManager
from utils.MigrateData import MigrateData

database_manager = KoalaDBManager("migrateTest.db", KoalaBot.DB_KEY, KoalaBot.CONFIG_DIR)
migrate_database = MigrateData(database_manager)


GUILD_EXTENSION_SELECT = "SELECT * FROM GuildExtensions"
GUILD_EXTENSION_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildExtensions'"

GUILD_WELCOME_MESSAGE_SELECT = "SELECT * FROM GuildWelcomeMessages"
GUILD_WELCOME_MESSAGE_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildWelcomeMessages'"

VOTES_SELECT = "SELECT * FROM Votes"
VOTES_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='Votes'"

VOTE_SENT_SELECT = "SELECT * FROM VoteSent"
VOTE_SENT_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='VoteSent'"

VOTE_OPTIONS_SELECT = "SELECT * FROM VoteOptions"
VOTE_OPTIONS_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='VoteOptions'"

VOTE_TARGET_ROLES_SELECT = "SELECT * FROM VoteTargetRoles"
VOTE_TARGET_ROLES_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='VoteTargetRoles'"

VERIFIED_EMAILS_OLD_SELECT = "SELECT * FROM verified_emails"
VERIFIED_EMAILS_OLD_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='verified_emails'"

VERIFIED_EMAILS_NEW_SELECT = "SELECT * FROM VerifiedEmails"
VERIFIED_EMAILS_NEW_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='VerifiedEmails'"

NON_VERIFIED_EMAILS_OLD_SELECT = "SELECT * FROM non_verified_emails"
NON_VERIFIED_EMAILS_OLD_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='non_verified_emails'"

NON_VERIFIED_EMAILS_NEW_SELECT = "SELECT * FROM NonVerifiedEmails"
NON_VERIFIED_EMAILS_NEW_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='NonVerifiedEmails'"

ROLES_OLD_SELECT = "SELECT * FROM roles"
ROLES_OLD_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='roles'"

ROLES_NEW_SELECT = "SELECT * FROM Roles"
ROLES_NEW_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='Roles'"

TO_RE_VERIFY_OLD_SELECT = "SELECT * FROM to_re_verify"
TO_RE_VERIFY_OLD_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='to_re_verify'"

TO_RE_VERIFY_NEW_SELECT = "SELECT * FROM ToReVerify"
TO_RE_VERIFY_NEW_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='ToReVerify'"

TWITCH_ALERTS_SELECT = "SELECT * FROM TwitchAlerts"
TWITCH_ALERTS_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TwitchAlerts'"

USER_IN_TWITCH_ALERT_SELECT = "SELECT * FROM UserInTwitchAlert"
USER_IN_TWITCH_ALERT_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='UserInTwitchAlert'"

TEAM_IN_TWITCH_ALERT_SELECT = "SELECT * FROM TeamInTwitchAlert"
TEAM_IN_TWITCH_ALERT_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TeamInTwitchAlert'"

USER_INT_TWITCH_TEAM_SELECT = "SELECT * FROM UserInTwitchTeam"
USER_INT_TWITCH_TEAM_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='UserInTwitchTeam'"

TEXT_FILTER_SELECT = "SELECT * FROM TextFilter"
TEXT_FILTER_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TextFilter'"

TEXT_FILTER_MODERATION_SELECT = "SELECT * FROM TextFilterModeration"
TEXT_FILTER_MODERATION_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TextFilterModeration'"

TEXT_FILTER_IGNORE_LIST_SELECT = "SELECT * FROM TextFilterIgnoreList"
TEXT_FILTER_IGNORE_LIST_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TextFilterIgnoreList'"

GUILD_RFR_MESSAGES_SELECT = "SELECT * FROM GuildRFRMessages"
GUILD_RFR_MESSAGES_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildRFRMessages'"

RFR_MESSAGE_EMOJI_ROLES_SELECT = "SELECT * FROM RFRMessageEmojiRoles"
RFR_MESSAGE_EMOJI_ROLES_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='RFRMessageEmojiRoles'"

GUILD_RFR_REQUIRED_ROLES_SELECT = "SELECT * FROM GuildRFRRequiredRoles"
GUILD_RFR_REQUIRED_ROLES_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildRFRRequiredRoles'"

GUILD_COLOUR_CHANGE_PERMISSIONS_SELECT = "SELECT * FROM GuildColourChangePermissions"
GUILD_COLOUR_CHANGE_PERMISSIONS_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildColourChangePermissions'"

GUILD_INVALID_CUSTOM_COLOUR_ROLES_SELECT = "SELECT * FROM GuildInvalidCustomColourRoles"
GUILD_INVALID_CUSTOM_COLOUR_ROLES_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildInvalidCustomColourRoles'"

GUILD_USAGE_SELECT = "SELECT * FROM GuildUsage"
GUILD_USAGE_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildUsage'"

GUILDS_SELECT = "SELECT * FROM Guilds"
GUILDS_COUNT = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='Guilds'"


def drop_table(table_name):
    sql = f"DROP TABLE IF EXISTS {table_name}"
    database_manager.db_execute_commit(sql)


def recursively_delete_dir(src):
    for child in src.iterdir():
        if child.is_file():
            child.unlink()
        else:
            recursively_delete_dir(child)
    src.rmdir()


def create_old_koala_extensions():
    sql_create_koala_extensions_table = """
        CREATE TABLE IF NOT EXISTS KoalaExtensions (
        extension_id text NOT NULL PRIMARY KEY,
        subscription_required integer NOT NULL,
        available boolean NOT NULL,
        enabled boolean NOT NULL
    );"""
    database_manager.db_execute_commit(sql_create_koala_extensions_table)


def populate_old_koala_extensions():
    koala_extension_data = [(1, 0, True, True), (2, 1, True, True), (3, 0, True, True)]
    for i in koala_extension_data:
        database_manager.db_execute_commit('INSERT INTO KoalaExtensions VALUES (?,?,?,?);', i)


def create_old_guild_extensions():
    create_old_koala_extensions()
    populate_old_koala_extensions()

    sql_create_guild_extensions_table = """
    CREATE TABLE IF NOT EXISTS GuildExtensions (
        extension_id text NOT NULL,
        guild_id integer NOT NULL,
        PRIMARY KEY (extension_id,guild_id),
        CONSTRAINT fk_extensions
            FOREIGN KEY (extension_id) 
            REFERENCES KoalaExtensions (extension_id)
            ON DELETE CASCADE 
    );"""
    database_manager.db_execute_commit(sql_create_guild_extensions_table)


def populate_old_guild_extensions():
    guild_extension_data = [(1, 1), (2, 1), (3, 1), (1, 2), (2, 2)]
    for i in guild_extension_data:
        database_manager.db_execute_commit('INSERT INTO GuildExtensions VALUES (?,?);', i)


def create_old_guild_welcome_message():
    sql_create_guild_welcome_messages_table = """
        CREATE TABLE IF NOT EXISTS GuildWelcomeMessages (
        guild_id integer NOT NULL PRIMARY KEY,
        welcome_message text
    );"""
    database_manager.db_execute_commit(sql_create_guild_welcome_messages_table)


def populate_old_guild_welcome_message():
    guild_welcome_messages_data = [(1, "This is a welcome message"), (2, "This is also a welcome message")]
    for i in guild_welcome_messages_data:
        database_manager.db_execute_commit('INSERT INTO GuildWelcomeMessages VALUES (?,?);', i)


def create_old_guild_usage():
    create_old_guild_extensions()
    populate_old_guild_extensions()

    sql_create_usage_tables = """
            CREATE TABLE IF NOT EXISTS GuildUsage (
            guild_id integer NOT NULL,
            last_message_epoch_time integer NOT NULL,
            PRIMARY KEY (guild_id),
            FOREIGN KEY (guild_id) REFERENCES GuildExtensions(guild_id)
            );
            """
    database_manager.db_execute_commit(sql_create_usage_tables)


def populate_old_guild_usage():
    guild_usage_data = [(1, 1), (2, 2)]
    for i in guild_usage_data:
        database_manager.db_execute_commit('INSERT INTO GuildUsage VALUES (?,?);', i)


def create_old_guild_colour_change_permissions():
    create_old_guild_extensions()
    populate_old_guild_extensions()

    sql_create_guild_colour_change_permissions_table = """
            CREATE TABLE IF NOT EXISTS GuildColourChangePermissions (
            guild_id integer NOT NULL,
            role_id integer NOT NULL,
            PRIMARY KEY (guild_id, role_id),
            FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
            );"""
    database_manager.db_execute_commit(sql_create_guild_colour_change_permissions_table)


def populate_old_guild_colour_change_permissions():
    guild_colour_change_permissions_data = [(1, 1), (1, 2), (2, 3), (2, 4)]
    for i in guild_colour_change_permissions_data:
        database_manager.db_execute_commit('INSERT INTO GuildColourChangePermissions VALUES (?,?);', i)


def create_old_guild_invalid_custom_colour_roles():
    create_old_guild_extensions()
    populate_old_guild_extensions()

    sql_create_guild_colour_change_invalid_colours_table = """
            CREATE TABLE IF NOT EXISTS GuildInvalidCustomColourRoles (
            guild_id integer NOT NULL,
            role_id integer NOT NULL,
            PRIMARY KEY (guild_id, role_id),
            FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
            );"""
    database_manager.db_execute_commit(sql_create_guild_colour_change_invalid_colours_table)


def populate_old_guild_invalid_custom_colour_roles():
    guild_invalid_custom_colour_roles_data = [(1, 5), (1, 6), (2, 7), (2, 8)]
    for i in guild_invalid_custom_colour_roles_data:
        database_manager.db_execute_commit('INSERT INTO GuildInvalidCustomColourRoles VALUES (?,?);', i)


def create_old_guild_rfr_messages():
    create_old_guild_extensions()
    populate_old_guild_extensions()

    sql_create_guild_rfr_message_ids_table = """
            CREATE TABLE IF NOT EXISTS GuildRFRMessages (
            guild_id integer NOT NULL,
            channel_id integer NOT NULL,
            message_id integer NOT NULL,
            emoji_role_id integer,
            PRIMARY KEY (emoji_role_id),
            FOREIGN KEY (guild_id) REFERENCES GuildExtensions(guild_id),
            UNIQUE (guild_id, channel_id, message_id)
            );
            """
    database_manager.db_execute_commit(sql_create_guild_rfr_message_ids_table)


def populate_old_guild_rfr_messages():
    guild_rfr_messages_data = [(1, 1, 1, 1), (1, 2, 2, 2), (2, 3, 3, 3), (2, 3, 4, 4)]
    for i in guild_rfr_messages_data:
        database_manager.db_execute_commit('INSERT INTO GuildRFRMessages VALUES (?,?,?,?);', i)


def create_old_rfr_message_emoji_roles():
    create_old_guild_rfr_messages()
    populate_old_guild_rfr_messages()

    sql_create_rfr_message_emoji_roles_table = """
            CREATE TABLE IF NOT EXISTS RFRMessageEmojiRoles (
            emoji_role_id integer NOT NULL,
            emoji_raw text NOT NULL,
            role_id integer NOT NULL,
            PRIMARY KEY (emoji_role_id, emoji_raw, role_id),
            FOREIGN KEY (emoji_role_id) REFERENCES GuildRFRMessages(emoji_role_id),
            UNIQUE (emoji_role_id, emoji_raw),
            UNIQUE  (emoji_role_id, role_id)
            );
            """
    database_manager.db_execute_commit(sql_create_rfr_message_emoji_roles_table)


def populate_old_rfr_message_emoji_roles():
    rfr_message_emoji_roles_data = [(1, "EMOJI1", 1), (2, "EMOJI2", 2), (3, "EMOJI3", 3), (4, "EMOJI4", 4)]
    for i in rfr_message_emoji_roles_data:
        database_manager.db_execute_commit('INSERT INTO RFRMessageEmojiRoles VALUES (?,?,?);', i)


def create_old_guild_rfr_required_roles():
    create_old_guild_extensions()
    populate_old_guild_extensions()

    sql_create_rfr_required_roles_table = """
            CREATE TABLE IF NOT EXISTS GuildRFRRequiredRoles (
            guild_id integer NOT NULL,
            role_id integer NOT NULL,
            PRIMARY KEY (guild_id, role_id),
            FOREIGN KEY (guild_id) REFERENCES GuildExtensions(guild_id),
            UNIQUE (guild_id, role_id)
            );
            """
    database_manager.db_execute_commit(sql_create_rfr_required_roles_table)


def populate_old_guild_rfr_required_roles():
    guild_rfr_required_roles_data = [(1, 1), (1, 2), (2, 3), (2, 4)]
    for i in guild_rfr_required_roles_data:
        database_manager.db_execute_commit('INSERT INTO GuildRFRRequiredRoles VALUES (?,?);', i)


def create_old_text_filter():
    sql_create_text_filter_table = """
            CREATE TABLE IF NOT EXISTS TextFilter (
            filtered_text_id text NOT NULL,
            guild_id integer NOT NULL,
            filtered_text text NOT NULL,
            filter_type text NOT NULL,
            is_regex boolean NOT NULL,
            PRIMARY KEY (filtered_text_id)
            );"""
    database_manager.db_execute_commit(sql_create_text_filter_table)


def populate_old_text_filter():
    text_filter_data = [("1", 1, "TEXT1", "TYPE1", True), ("2", 1, "TEXT2", "TYPE2", False),
                        ("3", 2, "TEXT3", "TYPE3", True), ("4", 2, "TEXT4", "TYPE4", False)]
    for i in text_filter_data:
        database_manager.db_execute_commit('INSERT INTO TextFilter VALUES (?,?,?,?,?);', i)


def create_old_text_filter_moderation():
    sql_create_mod_table = """
            CREATE TABLE IF NOT EXISTS TextFilterModeration (
            channel_id text NOT NULL,
            guild_id integer NOT NULL,
            PRIMARY KEY (channel_id)
            );"""
    database_manager.db_execute_commit(sql_create_mod_table)


def populate_old_text_filter_moderation():
    text_filter_moderation_data = [("1", 1), ("2", 1), ("3", 2), ("4", 2)]
    for i in text_filter_moderation_data:
        database_manager.db_execute_commit('INSERT INTO TextFilterModeration VALUES (?,?);', i)


def create_old_text_filter_ignore_list():
    sql_create_ignore_list_table = """
            CREATE TABLE IF NOT EXISTS TextFilterIgnoreList (
            ignore_id text NOT NULL,
            guild_id integer NOT NULL,
            ignore_type text NOT NULL,
            ignore integer NOT NULL,
            PRIMARY KEY (ignore_id)
            );"""
    database_manager.db_execute_commit(sql_create_ignore_list_table)


def populate_old_text_filter_ignore_list():
    text_filter_ignore_list_data = [("1", 1, "TYPE1", 1), ("2", 1, "TYPE2", 1), ("3", 2, "TYPE3", 1),
                                    ("4", 2, "TYPE4", 1)]
    for i in text_filter_ignore_list_data:
        database_manager.db_execute_commit('INSERT INTO TextFilterIgnoreList VALUES (?,?,?,?);', i)


def create_old_twitch_alerts():
    create_old_guild_extensions()
    populate_old_guild_extensions()

    sql_create_twitch_alerts_table = """
            CREATE TABLE IF NOT EXISTS TwitchAlerts (
            guild_id integer NOT NULL,
            channel_id integer NOT NULL,
            default_message text NOT NULL,
            PRIMARY KEY (guild_id, channel_id),
            CONSTRAINT fk_guild
                FOREIGN KEY (guild_id) 
                REFERENCES GuildExtensions (guild_id)
                ON DELETE CASCADE 
            );"""
    database_manager.db_execute_commit(sql_create_twitch_alerts_table)


def populate_old_twitch_alerts():
    twitch_alerts_data = [(1, 1, "MESSAGE1"), (1, 2, "MESSAGE2"), (2, 3, "MESSAGE3"), (2, 4, "MESSAGE4")]
    for i in twitch_alerts_data:
        database_manager.db_execute_commit('INSERT INTO TwitchAlerts VALUES (?,?,?);', i)


def create_old_user_in_twitch_alerts():
    create_old_twitch_alerts()
    populate_old_twitch_alerts()

    sql_create_user_in_twitch_alert_table = """
            CREATE TABLE IF NOT EXISTS UserInTwitchAlert (
            channel_id integer NOT NULL,
            twitch_username text NOT NULL,
            custom_message text,
            message_id integer,
            PRIMARY KEY (channel_id, twitch_username),
            CONSTRAINT fk_channel
                FOREIGN KEY (channel_id) 
                REFERENCES TwitchAlerts (channel_id)
                ON DELETE CASCADE 
            );"""
    database_manager.db_execute_commit(sql_create_user_in_twitch_alert_table)


def populate_old_user_in_twitch_alerts():
    user_in_twitch_alerts_data = [(1, "USERNAME1", "MESSAGE1", 1), (2, "USERNAME2", "MESSAGE2", 2),
                                  (3, "USERNAME3", "MESSAGE3", 3), (4, "USERNAME4", "MESSAGE4", 4)]
    for i in user_in_twitch_alerts_data:
        database_manager.db_execute_commit('INSERT INTO UserInTwitchAlert VALUES (?,?,?,?);', i)


def create_old_team_in_twitch_alerts():
    create_old_twitch_alerts()
    populate_old_twitch_alerts()

    sql_create_team_in_twitch_alert_table = """
            CREATE TABLE IF NOT EXISTS TeamInTwitchAlert (
            team_twitch_alert_id integer PRIMARY KEY AUTOINCREMENT, 
            channel_id integer NOT NULL,
            twitch_team_name text NOT NULL,
            custom_message text,
            CONSTRAINT fk_channel
                FOREIGN KEY (channel_id) 
                REFERENCES TwitchAlerts (channel_id)
                ON DELETE CASCADE 
            );"""
    database_manager.db_execute_commit(sql_create_team_in_twitch_alert_table)


def populate_old_team_in_twitch_alerts():
    team_in_twitch_alerts_data = [(1, "TEAM_NAME1", "MESSAGE1"), (2, "TEAM_NAME2", "MESSAGE2"),
                                  (3, "TEAM_NAME3", "MESSAGE3"), (4, "TEAM_NAME4", "MESSAGE4")]
    for i in team_in_twitch_alerts_data:
        database_manager.db_execute_commit(
            'INSERT INTO TeamInTwitchAlert (channel_id, twitch_team_name, custom_message) VALUES (?,?,?);', i)


def create_old_user_in_twitch_team():
    create_old_team_in_twitch_alerts()
    populate_old_team_in_twitch_alerts()

    sql_create_user_in_twitch_team_table = """
            CREATE TABLE IF NOT EXISTS UserInTwitchTeam (
            team_twitch_alert_id text NOT NULL,
            twitch_username text NOT NULL,
            message_id integer,
            PRIMARY KEY (team_twitch_alert_id, twitch_username),
            CONSTRAINT fk_twitch_team_alert
                FOREIGN KEY (team_twitch_alert_id) 
                REFERENCES TeamInTwitchAlert (team_twitch_alert_id)
                ON DELETE CASCADE 
            );"""
    database_manager.db_execute_commit(sql_create_user_in_twitch_team_table)


def populate_old_user_in_twitch_team():
    user_in_twitch_team_data = [("1", "USERNAME1", 1), ("2", "USERNAME2", 2), ("3", "USERNAME3", 3),
                                ("4", "USERNAME4", 4)]
    for i in user_in_twitch_team_data:
        database_manager.db_execute_commit('INSERT INTO UserInTwitchTeam VALUES (?,?,?);', i)


def create_old_verified_emails():
    verified_table = """
            CREATE TABLE IF NOT EXISTS verified_emails (
            u_id integer NOT NULL,
            email text NOT NULL,
            PRIMARY KEY (u_id, email)
            );"""
    database_manager.db_execute_commit(verified_table)


def populate_old_verified_emails():
    verified_emails_data = [(1, "EMAIL1"), (2, "EMAIL2"), (3, "EMAIL3"), (4, "EMAIL4")]
    for i in verified_emails_data:
        database_manager.db_execute_commit('INSERT INTO verified_emails VALUES (?,?);', i)


def create_old_non_verified_emails():
    non_verified_table = """
            CREATE TABLE IF NOT EXISTS non_verified_emails (
            u_id integer NOT NULL,
            email text NOT NULL,
            token text NOT NULL,
            PRIMARY KEY (token)
            );"""
    database_manager.db_execute_commit(non_verified_table)


def populate_old_non_verified_emails():
    not_verified_emails_data = [(5, "EMAIL5", "TOKEN5"), (6, "EMAIL6", "TOKEN6"), (7, "EMAIL7", "TOKEN7"),
                                (8, "EMAIL8", "TOKEN8")]
    for i in not_verified_emails_data:
        database_manager.db_execute_commit('INSERT INTO non_verified_emails VALUES (?,?,?);', i)


def create_old_roles():
    create_old_guild_extensions()
    populate_old_guild_extensions()

    role_table = """
            CREATE TABLE IF NOT EXISTS roles (
            s_id integer NOT NULL,
            r_id integer NOT NULL,
            email_suffix text NOT NULL,
            PRIMARY KEY (s_id, r_id, email_suffix),
            FOREIGN KEY (s_id) REFERENCES GuildExtensions (guild_id)
            );"""
    database_manager.db_execute_commit(role_table)


def populate_old_roles():
    roles_data = [(1, 1, "EMAIL_SUFFIX1"), (1, 2, "EMAIL_SUFFIX2"), (2, 3, "EMAIL_SUFFIX3"), (2, 4, "EMAIL_SUFFIX4")]
    for i in roles_data:
        database_manager.db_execute_commit('INSERT INTO roles VALUES (?,?,?);', i)


def create_old_to_re_verify():
    re_verify_table = """
            CREATE TABLE IF NOT EXISTS to_re_verify (
            u_id integer NOT NULL,
            r_id text NOT NULL,
            PRIMARY KEY (u_id, r_id)
            );"""
    database_manager.db_execute_commit(re_verify_table)


def populate_old_to_re_verify():
    to_re_verify_data = [(1, 1), (2, 2)]
    for i in to_re_verify_data:
        database_manager.db_execute_commit('INSERT INTO to_re_verify VALUES (?,?);', i)


def create_old_votes():
    vote_table = """
            CREATE TABLE IF NOT EXISTS Votes (
            vote_id integer NOT NULL,
            author_id integer NOT NULL,
            guild_id integer NOT NULL,
            title text NOT NULL,
            chair_id integer,
            voice_id integer,
            end_time float
            );"""
    database_manager.db_execute_commit(vote_table)


def populate_old_votes():
    votes_data = [(1, 1, 1, "VOTE1", 1, 1, 0), (2, 1, 1, "VOTE2", 2, 2, 0), (3, 2, 2, "VOTE3", 3, 3, 0),
                  (4, 2, 2, "VOTE4", 4, 4, 0)]
    for i in votes_data:
        database_manager.db_execute_commit('INSERT INTO Votes VALUES (?,?,?,?,?,?,?);', i)


def create_old_vote_target_roles():
    role_table = """
            CREATE TABLE IF NOT EXISTS VoteTargetRoles (
            vote_id integer NOT NULL,
            role_id integer NOT NULL
            );"""
    database_manager.db_execute_commit(role_table)


def populate_old_vote_target_roles():
    vote_target_roles_data = [(1, 1), (2, 2), (3, 3), (4, 4)]
    for i in vote_target_roles_data:
        database_manager.db_execute_commit('INSERT INTO VoteTargetRoles VALUES (?,?);', i)


def create_old_vote_options():
    option_table = """
            CREATE TABLE IF NOT EXISTS VoteOptions (
            vote_id integer NOT NULL,
            opt_id integer NOT NULL,
            option_title text NOT NULL,
            option_desc text NOT NULL
            );"""
    database_manager.db_execute_commit(option_table)


def populate_old_vote_options():
    vote_options_data = [(1, 1, "TITLE1", "DESCRIPTION1"), (2, 2, "TITLE2", "DESCRIPTION2"),
                         (3, 3, "TITLE3", "DESCRIPTION3"), (4, 4, "TITLE4", "DESCRIPTION4")]
    for i in vote_options_data:
        database_manager.db_execute_commit('INSERT INTO VoteOptions VALUES (?,?,?,?);', i)


def create_old_vote_sent():
    delivered_table = """
            CREATE TABLE IF NOT EXISTS VoteSent (
            vote_id integer NOT NULL,
            vote_receiver_id integer NOT NULL,
            vote_receiver_message integer NOT NULL
            );"""
    database_manager.db_execute_commit(delivered_table)


def populate_old_vote_sent():
    vote_sent_data = [(1, 5, "MESSAGE1"), (2, 6, "MESSAGE2"), (3, 7, "MESSAGE3"), (4, 8, "MESSAGE4")]
    for i in vote_sent_data:
        database_manager.db_execute_commit('INSERT INTO VoteSent VALUES (?,?,?);', i)


def create_guilds():
    guilds_table = """
            CREATE TABLE IF NOT EXISTS Guilds (
            guild_id text NOT NULL,
            subscription integer NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id)
            );"""
    database_manager.db_execute_commit(guilds_table)


def populate_guilds():
    guilds_data = [(1, 0), (2, 1)]
    for i in guilds_data:
        database_manager.db_execute_commit('INSERT INTO Guilds VALUES (?,?);', i)


@pytest.mark.asyncio()
async def test_remake_guild_extensions():
    drop_table("GuildExtensions")
    create_old_guild_extensions()
    populate_old_guild_extensions()

    before_expected_result = [('1', 1), ('2', 1), ('3', 1), ('1', 2), ('2', 2)]
    before_data_stored = database_manager.db_execute_select(GUILD_EXTENSION_SELECT)
    assert before_expected_result == before_data_stored
    migrate_database.remake_guild_extensions()
    after_expected_result = [('1', '1'), ('2', '1'), ('3', '1'), ('1', '2'), ('2', '2')]
    after_data_stored = database_manager.db_execute_select(GUILD_EXTENSION_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("GuildExtensions")
    create_old_guild_extensions()


@pytest.mark.asyncio()
async def test_remake_guilds_extensions_no_table():
    drop_table("GuildExtensions")

    count_before = database_manager.db_execute_select(GUILD_EXTENSION_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_guild_extensions()
    count_after = database_manager.db_execute_select(GUILD_EXTENSION_COUNT)
    assert 1 == count_after[0][0]

    drop_table("GuildExtensions")
    create_old_guild_extensions()


@pytest.mark.asyncio()
async def test_remake_guild_welcome_message():
    drop_table("GuildWelcomeMessages")
    create_old_guild_welcome_message()
    populate_old_guild_welcome_message()

    before_expected_result = [(1, "This is a welcome message"), (2, "This is also a welcome message")]
    before_data_stored = database_manager.db_execute_select(GUILD_WELCOME_MESSAGE_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_guild_welcome_messages()
    after_expected_result = [("1", "This is a welcome message"), ("2", "This is also a welcome message")]
    after_data_stored = database_manager.db_execute_select(GUILD_WELCOME_MESSAGE_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("GuildWelcomeMessages")
    create_old_guild_welcome_message()


@pytest.mark.asyncio()
async def test_remake_guild_welcome_message_no_table():
    drop_table("GuildWelcomeMessages")

    count_before = database_manager.db_execute_select(GUILD_WELCOME_MESSAGE_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_guild_welcome_messages()
    count_after = database_manager.db_execute_select(GUILD_WELCOME_MESSAGE_COUNT)
    assert 1 == count_after[0][0]

    drop_table("GuildWelcomeMessages")
    create_old_guild_welcome_message()


@pytest.mark.asyncio()
async def test_remake_votes():
    drop_table("Votes")
    create_old_votes()
    populate_old_votes()

    before_expected_result = [(1, 1, 1, "VOTE1", 1, 1, 0), (2, 1, 1, "VOTE2", 2, 2, 0), (3, 2, 2, "VOTE3", 3, 3, 0),
                              (4, 2, 2, "VOTE4", 4, 4, 0)]
    before_data_stored = database_manager.db_execute_select(VOTES_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_votes()
    after_expected_result = [("1", "1", "1", "VOTE1", "1", "1", 0), ("2", "1", "1", "VOTE2", "2", "2", 0),
                             ("3", "2", "2", "VOTE3", "3", "3", 0), ("4", "2", "2", "VOTE4", "4", "4", 0)]
    after_data_stored = database_manager.db_execute_select(VOTES_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("Votes")
    create_old_votes()


@pytest.mark.asyncio()
async def test_remake_votes_no_table():
    drop_table("Votes")

    count_before = database_manager.db_execute_select(VOTES_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_votes()
    count_after = database_manager.db_execute_select(VOTES_COUNT)
    assert 1 == count_after[0][0]

    drop_table("Votes")
    create_old_votes()


@pytest.mark.asyncio()
async def test_remake_vote_sent():
    drop_table("VoteSent")
    create_old_vote_sent()
    populate_old_vote_sent()

    before_expected_result = [(1, 5, "MESSAGE1"), (2, 6, "MESSAGE2"), (3, 7, "MESSAGE3"), (4, 8, "MESSAGE4")]
    before_data_stored = database_manager.db_execute_select(VOTE_SENT_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_vote_sent()
    after_expected_result = [("1", "5", "MESSAGE1"), ("2", "6", "MESSAGE2"), ("3", "7", "MESSAGE3"),
                             ("4", "8", "MESSAGE4")]
    after_data_stored = database_manager.db_execute_select(VOTE_SENT_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("VoteSent")
    create_old_vote_sent()


@pytest.mark.asyncio()
async def test_remake_vote_sent_no_table():
    drop_table("VoteSent")

    count_before = database_manager.db_execute_select(VOTE_SENT_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_vote_sent()
    count_after = database_manager.db_execute_select(VOTE_SENT_COUNT)
    assert 1 == count_after[0][0]

    drop_table("VoteSent")
    create_old_vote_sent()


@pytest.mark.asyncio()
async def test_remake_vote_options():
    drop_table("VoteOptions")
    create_old_vote_options()
    populate_old_vote_options()

    before_expected_result = [(1, 1, "TITLE1", "DESCRIPTION1"), (2, 2, "TITLE2", "DESCRIPTION2"),
                              (3, 3, "TITLE3", "DESCRIPTION3"), (4, 4, "TITLE4", "DESCRIPTION4")]
    before_data_stored = database_manager.db_execute_select(VOTE_OPTIONS_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_vote_options()
    after_expected_result = [("1", "1", "TITLE1", "DESCRIPTION1"), ("2", "2", "TITLE2", "DESCRIPTION2"),
                             ("3", "3", "TITLE3", "DESCRIPTION3"), ("4", "4", "TITLE4", "DESCRIPTION4")]
    after_data_stored = database_manager.db_execute_select(VOTE_OPTIONS_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("GuildExtensions")
    create_old_vote_options()


@pytest.mark.asyncio()
async def test_remake_vote_options_no_table():
    drop_table("VoteOptions")

    count_before = database_manager.db_execute_select(VOTE_OPTIONS_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_vote_options()
    count_after = database_manager.db_execute_select(VOTE_OPTIONS_COUNT)
    assert 1 == count_after[0][0]

    drop_table("VoteOptions")
    create_old_vote_options()


@pytest.mark.asyncio()
async def test_remake_vote_target_roles():
    drop_table("VoteTargetRoles")
    create_old_vote_target_roles()
    populate_old_vote_target_roles()

    before_expected_result = [(1, 1), (2, 2), (3, 3), (4, 4)]
    before_data_stored = database_manager.db_execute_select(VOTE_TARGET_ROLES_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_vote_target_roles()
    after_expected_result = [("1", "1"), ("2", "2"), ("3", "3"), ("4", "4")]
    after_data_stored = database_manager.db_execute_select(VOTE_TARGET_ROLES_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("VoteTargetRoles")
    create_old_vote_target_roles()


@pytest.mark.asyncio()
async def test_remake_vote_target_roles_no_table():
    drop_table("VoteTargetRoles")

    count_before = database_manager.db_execute_select(VOTE_TARGET_ROLES_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_vote_target_roles()
    count_after = database_manager.db_execute_select(VOTE_TARGET_ROLES_COUNT)
    assert 1 == count_after[0][0]

    drop_table("VoteTargetRoles")
    create_old_vote_target_roles()


@pytest.mark.asyncio()
async def test_remake_verified_emails_old_name():
    drop_table("verified_emails")
    drop_table("VerifiedEmails")
    create_old_verified_emails()
    populate_old_verified_emails()

    before_expected_result = [(1, "EMAIL1"), (2, "EMAIL2"), (3, "EMAIL3"), (4, "EMAIL4")]
    before_data_stored = database_manager.db_execute_select(VERIFIED_EMAILS_OLD_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_verified_emails()
    after_expected_result = [("1", "EMAIL1"), ("2", "EMAIL2"), ("3", "EMAIL3"), ("4", "EMAIL4")]
    after_data_stored = database_manager.db_execute_select(VERIFIED_EMAILS_NEW_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("VerifiedEmails")
    create_old_verified_emails()


@pytest.mark.asyncio()
async def test_remake_verified_emails_old_name_no_table():
    drop_table("verified_emails")
    drop_table("VerifiedEmails")

    count_before = database_manager.db_execute_select(VERIFIED_EMAILS_NEW_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_verified_emails()
    count_wrong_name = database_manager.db_execute_select(VERIFIED_EMAILS_OLD_COUNT)
    assert 0 == count_wrong_name[0][0]
    count_after = database_manager.db_execute_select(VERIFIED_EMAILS_NEW_COUNT)
    assert 1 == count_after[0][0]

    drop_table("VerifiedEmails")
    create_old_verified_emails()


@pytest.mark.asyncio()
async def test_remake_verified_emails_new_name():
    drop_table("verified_emails")
    drop_table("VerifiedEmails")
    create_old_verified_emails()
    populate_old_verified_emails()

    # Shows the script will alter the table even if the table has the new naming scheme.
    database_manager.db_execute_commit("""ALTER TABLE verified_emails RENAME TO VerifiedEmails;""")
    before_expected_result = [(1, "EMAIL1"), (2, "EMAIL2"), (3, "EMAIL3"), (4, "EMAIL4")]
    before_data_stored = database_manager.db_execute_select(VERIFIED_EMAILS_NEW_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_verified_emails()
    after_expected_result = [("1", "EMAIL1"), ("2", "EMAIL2"), ("3", "EMAIL3"), ("4", "EMAIL4")]
    after_data_stored = database_manager.db_execute_select(VERIFIED_EMAILS_NEW_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("VerifiedEmails")
    create_old_verified_emails()


@pytest.mark.asyncio()
async def test_remake_verified_emails_new_name_no_table():
    drop_table("verified_emails")
    drop_table("VerifiedEmails")

    count_before = database_manager.db_execute_select(VERIFIED_EMAILS_NEW_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_verified_emails()
    count_after = database_manager.db_execute_select(VERIFIED_EMAILS_NEW_COUNT)
    assert 1 == count_after[0][0]

    drop_table("VerifiedEmails")
    create_old_verified_emails()


@pytest.mark.asyncio()
async def test_remake_not_verified_emails_old_name():
    drop_table("non_verified_emails")
    drop_table("NonVerifiedEmails")
    create_old_non_verified_emails()
    populate_old_non_verified_emails()

    before_expected_result = [(5, "EMAIL5", "TOKEN5"), (6, "EMAIL6", "TOKEN6"), (7, "EMAIL7", "TOKEN7"),
                              (8, "EMAIL8", "TOKEN8")]
    before_data_stored = database_manager.db_execute_select(NON_VERIFIED_EMAILS_OLD_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_not_verified_emails()
    after_expected_result = [("5", "EMAIL5", "TOKEN5"), ("6", "EMAIL6", "TOKEN6"), ("7", "EMAIL7", "TOKEN7"),
                             ("8", "EMAIL8", "TOKEN8")]
    after_data_stored = database_manager.db_execute_select(NON_VERIFIED_EMAILS_NEW_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("NonVerifiedEmails")
    create_old_non_verified_emails()


@pytest.mark.asyncio()
async def test_remake_not_verified_emails_old_name_no_table():
    drop_table("non_verified_emails")
    drop_table("NonVerifiedEmails")

    count_before = database_manager.db_execute_select(NON_VERIFIED_EMAILS_NEW_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_not_verified_emails()
    count_wrong_name = database_manager.db_execute_select(NON_VERIFIED_EMAILS_OLD_COUNT)
    assert 0 == count_wrong_name[0][0]
    count_after = database_manager.db_execute_select(NON_VERIFIED_EMAILS_NEW_COUNT)
    assert 1 == count_after[0][0]

    drop_table("NonVerifiedEmails")
    create_old_non_verified_emails()


@pytest.mark.asyncio()
async def test_remake_not_verified_emails_new_name():
    drop_table("non_verified_emails")
    drop_table("NonVerifiedEmails")
    create_old_non_verified_emails()
    populate_old_non_verified_emails()

    database_manager.db_execute_commit("""ALTER TABLE non_verified_emails RENAME TO NonVerifiedEmails;""")
    before_expected_result = [(5, "EMAIL5", "TOKEN5"), (6, "EMAIL6", "TOKEN6"), (7, "EMAIL7", "TOKEN7"),
                              (8, "EMAIL8", "TOKEN8")]
    before_data_stored = database_manager.db_execute_select(NON_VERIFIED_EMAILS_NEW_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_not_verified_emails()
    after_expected_result = [("5", "EMAIL5", "TOKEN5"), ("6", "EMAIL6", "TOKEN6"), ("7", "EMAIL7", "TOKEN7"),
                             ("8", "EMAIL8", "TOKEN8")]
    after_data_stored = database_manager.db_execute_select(NON_VERIFIED_EMAILS_NEW_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("NonVerifiedEmails")
    create_old_non_verified_emails()


@pytest.mark.asyncio()
async def test_remake_not_verified_emails_new_name_no_table():
    drop_table("non_verified_emails")
    drop_table("NonVerifiedEmails")

    count_before = database_manager.db_execute_select(NON_VERIFIED_EMAILS_NEW_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_not_verified_emails()
    count_after = database_manager.db_execute_select(NON_VERIFIED_EMAILS_NEW_COUNT)
    assert 1 == count_after[0][0]

    drop_table("NonVerifiedEmails")
    create_old_non_verified_emails()


@pytest.mark.asyncio()
async def test_remake_role_old_name():
    drop_table("roles")
    drop_table("Roles")
    create_old_roles()
    populate_old_roles()

    before_expected_result = [(1, 1, "EMAIL_SUFFIX1"), (1, 2, "EMAIL_SUFFIX2"), (2, 3, "EMAIL_SUFFIX3"),
                              (2, 4, "EMAIL_SUFFIX4")]
    before_data_stored = database_manager.db_execute_select(ROLES_OLD_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_role_table()
    after_expected_result = [("1", "1", "EMAIL_SUFFIX1"), ("1", "2", "EMAIL_SUFFIX2"), ("2", "3", "EMAIL_SUFFIX3"),
                             ("2", "4", "EMAIL_SUFFIX4")]
    after_data_stored = database_manager.db_execute_select(ROLES_NEW_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("Roles")
    create_old_roles()


@pytest.mark.asyncio()
async def test_remake_role_old_name_no_table():
    drop_table("roles")
    drop_table("Roles")

    count_before = database_manager.db_execute_select(ROLES_NEW_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_role_table()
    count_wrong_name = database_manager.db_execute_select(ROLES_OLD_COUNT)
    assert 0 == count_wrong_name[0][0]
    count_after = database_manager.db_execute_select(ROLES_NEW_COUNT)
    assert 1 == count_after[0][0]

    drop_table("Roles")
    create_old_roles()


@pytest.mark.asyncio()
async def test_remake_role_new_name():
    drop_table("roles")
    drop_table("Roles")
    create_old_roles()
    populate_old_roles()

    database_manager.db_execute_commit("""ALTER TABLE roles RENAME TO Roles;""")
    before_expected_result = [(1, 1, "EMAIL_SUFFIX1"), (1, 2, "EMAIL_SUFFIX2"), (2, 3, "EMAIL_SUFFIX3"),
                              (2, 4, "EMAIL_SUFFIX4")]
    before_data_stored = database_manager.db_execute_select(ROLES_NEW_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_role_table()
    after_expected_result = [("1", "1", "EMAIL_SUFFIX1"), ("1", "2", "EMAIL_SUFFIX2"), ("2", "3", "EMAIL_SUFFIX3"),
                             ("2", "4", "EMAIL_SUFFIX4")]
    after_data_stored = database_manager.db_execute_select(ROLES_NEW_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("Roles")
    create_old_roles()


@pytest.mark.asyncio()
async def test_remake_role_new_name_no_table():
    drop_table("roles")
    drop_table("Roles")

    count_before = database_manager.db_execute_select(ROLES_NEW_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_role_table()
    count_after = database_manager.db_execute_select(ROLES_NEW_COUNT)
    assert 1 == count_after[0][0]

    drop_table("Roles")
    create_old_roles()


@pytest.mark.asyncio()
async def test_remake_to_re_verify_old_name():
    drop_table("to_re_verify")
    drop_table("ToReVerify")
    create_old_to_re_verify()
    populate_old_to_re_verify()

    before_expected_result = [(1, "1"), (2, "2")]
    before_data_stored = database_manager.db_execute_select(TO_RE_VERIFY_OLD_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_to_re_verify()
    after_expected_result = [("1", "1"), ("2", "2")]
    after_data_stored = database_manager.db_execute_select(TO_RE_VERIFY_NEW_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("ToReVerify")
    create_old_to_re_verify()


@pytest.mark.asyncio()
async def test_remake_to_re_verify_old_name_no_table():
    drop_table("to_re_verify")
    drop_table("ToReVerify")

    count_before = database_manager.db_execute_select(TO_RE_VERIFY_NEW_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_to_re_verify()
    count_wrong_name = database_manager.db_execute_select(TO_RE_VERIFY_OLD_COUNT)
    assert 0 == count_wrong_name[0][0]
    count_after = database_manager.db_execute_select(TO_RE_VERIFY_NEW_COUNT)
    assert 1 == count_after[0][0]

    drop_table("ToReVerify")
    create_old_to_re_verify()


@pytest.mark.asyncio()
async def test_remake_to_re_verify_new_name():
    drop_table("to_re_verify")
    drop_table("ToReVerify")
    create_old_to_re_verify()
    populate_old_to_re_verify()

    database_manager.db_execute_commit("""ALTER TABLE to_re_verify RENAME TO ToReVerify;""")
    before_expected_result = [(1, "1"), (2, "2")]
    before_data_stored = database_manager.db_execute_select(TO_RE_VERIFY_NEW_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_to_re_verify()
    after_expected_result = [("1", "1"), ("2", "2")]
    after_data_stored = database_manager.db_execute_select(TO_RE_VERIFY_NEW_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("ToReVerify")
    create_old_to_re_verify()


@pytest.mark.asyncio()
async def test_remake_to_re_verify_new_name_no_table():
    drop_table("to_re_verify")
    drop_table("ToReVerify")

    count_before = database_manager.db_execute_select(TO_RE_VERIFY_NEW_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_to_re_verify()
    count_after = database_manager.db_execute_select(TO_RE_VERIFY_NEW_COUNT)
    assert 1 == count_after[0][0]

    drop_table("ToReVerify")
    create_old_to_re_verify()


@pytest.mark.asyncio()
async def test_remake_twitch_alert():
    drop_table("TwitchAlerts")
    create_old_twitch_alerts()
    populate_old_twitch_alerts()

    before_expected_result = [(1, 1, "MESSAGE1"), (1, 2, "MESSAGE2"), (2, 3, "MESSAGE3"), (2, 4, "MESSAGE4")]
    before_data_stored = database_manager.db_execute_select(TWITCH_ALERTS_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_twitch_alerts()
    after_expected_result = [("1", "1", "MESSAGE1"), ("1", "2", "MESSAGE2"), ("2", "3", "MESSAGE3"),
                             ("2", "4", "MESSAGE4")]
    after_data_stored = database_manager.db_execute_select(TWITCH_ALERTS_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("TwitchAlerts")
    create_old_twitch_alerts()


@pytest.mark.asyncio()
async def test_remake_twitch_alert_no_table():
    drop_table("TwitchAlerts")

    count_before = database_manager.db_execute_select(TWITCH_ALERTS_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_twitch_alerts()
    count_after = database_manager.db_execute_select(TWITCH_ALERTS_COUNT)
    assert 1 == count_after[0][0]

    drop_table("TwitchAlerts")
    create_old_twitch_alerts()


@pytest.mark.asyncio()
async def test_remake_user_in_twitch_alert():
    drop_table("UserInTwitchAlert")
    create_old_user_in_twitch_alerts()
    populate_old_user_in_twitch_alerts()

    before_expected_result = [(1, "USERNAME1", "MESSAGE1", 1), (2, "USERNAME2", "MESSAGE2", 2),
                              (3, "USERNAME3", "MESSAGE3", 3), (4, "USERNAME4", "MESSAGE4", 4)]
    before_data_stored = database_manager.db_execute_select(USER_IN_TWITCH_ALERT_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_user_in_twitch_alert()
    after_expected_result = [("1", "USERNAME1", "MESSAGE1", "1"), ("2", "USERNAME2", "MESSAGE2", "2"),
                             ("3", "USERNAME3", "MESSAGE3", "3"), ("4", "USERNAME4", "MESSAGE4", "4")]
    after_data_stored = database_manager.db_execute_select(USER_IN_TWITCH_ALERT_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("UserInTwitchAlert")
    create_old_user_in_twitch_alerts()


@pytest.mark.asyncio()
async def test_remake_user_in_twitch_alert_no_table():
    drop_table("UserInTwitchAlert")

    count_before = database_manager.db_execute_select(USER_IN_TWITCH_ALERT_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_user_in_twitch_alert()
    count_after = database_manager.db_execute_select(USER_IN_TWITCH_ALERT_COUNT)
    assert 1 == count_after[0][0]

    drop_table("UserInTwitchAlert")
    create_old_user_in_twitch_alerts()


@pytest.mark.asyncio()
async def test_remake_team_in_twitch_alert():
    drop_table("TeamInTwitchAlert")
    create_old_team_in_twitch_alerts()
    populate_old_team_in_twitch_alerts()

    before_expected_result = [(1, 1, "TEAM_NAME1", "MESSAGE1"), (2, 2, "TEAM_NAME2", "MESSAGE2"),
                              (3, 3, "TEAM_NAME3", "MESSAGE3"), (4, 4, "TEAM_NAME4", "MESSAGE4")]
    before_data_stored = database_manager.db_execute_select(TEAM_IN_TWITCH_ALERT_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_team_in_twitch_alert()
    after_expected_result = [(1, "1", "TEAM_NAME1", "MESSAGE1"), (2, "2", "TEAM_NAME2", "MESSAGE2"),
                             (3, "3", "TEAM_NAME3", "MESSAGE3"), (4, "4", "TEAM_NAME4", "MESSAGE4")]
    after_data_stored = database_manager.db_execute_select(TEAM_IN_TWITCH_ALERT_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("TeamInTwitchAlert")
    create_old_team_in_twitch_alerts()


@pytest.mark.asyncio()
async def test_remake_team_in_twitch_alert_no_table():
    drop_table("TeamInTwitchAlert")

    count_before = database_manager.db_execute_select(TEAM_IN_TWITCH_ALERT_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_team_in_twitch_alert()
    count_after = database_manager.db_execute_select(TEAM_IN_TWITCH_ALERT_COUNT)
    assert 1 == count_after[0][0]

    drop_table("TeamInTwitchAlert")
    create_old_team_in_twitch_alerts()


@pytest.mark.asyncio()
async def test_remake_user_in_twitch_team():
    drop_table("UserInTwitchTeam")
    create_old_user_in_twitch_team()
    populate_old_user_in_twitch_team()

    before_expected_result = [("1", "USERNAME1", 1), ("2", "USERNAME2", 2), ("3", "USERNAME3", 3),
                              ("4", "USERNAME4", 4)]
    before_data_stored = database_manager.db_execute_select(USER_INT_TWITCH_TEAM_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_user_in_twitch_team()
    after_expected_result = [("1", "USERNAME1", "1"), ("2", "USERNAME2", "2"), ("3", "USERNAME3", "3"),
                             ("4", "USERNAME4", "4")]
    after_data_stored = database_manager.db_execute_select(USER_INT_TWITCH_TEAM_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("UserInTwitchTeam")
    create_old_user_in_twitch_team()


@pytest.mark.asyncio()
async def test_remake_user_in_twitch_team_no_table():
    drop_table("UserInTwitchTeam")

    count_before = database_manager.db_execute_select(USER_INT_TWITCH_TEAM_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_user_in_twitch_team()
    count_after = database_manager.db_execute_select(USER_INT_TWITCH_TEAM_COUNT)
    assert 1 == count_after[0][0]

    drop_table("UserInTwitchTeam")
    create_old_user_in_twitch_team()


@pytest.mark.asyncio()
async def test_remake_text_filter():
    drop_table("TextFilter")
    create_old_text_filter()
    populate_old_text_filter()

    before_expected_result = [("1", 1, "TEXT1", "TYPE1", True), ("2", 1, "TEXT2", "TYPE2", False),
                              ("3", 2, "TEXT3", "TYPE3", True), ("4", 2, "TEXT4", "TYPE4", False)]
    before_data_stored = database_manager.db_execute_select(TEXT_FILTER_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_text_filter()
    after_expected_result = [("1", "1", "TEXT1", "TYPE1", True), ("2", "1", "TEXT2", "TYPE2", False),
                             ("3", "2", "TEXT3", "TYPE3", True), ("4", "2", "TEXT4", "TYPE4", False)]
    after_data_stored = database_manager.db_execute_select(TEXT_FILTER_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("TextFilter")
    create_old_text_filter()


@pytest.mark.asyncio()
async def test_remake_text_filter_no_table():
    drop_table("TextFilter")

    count_before = database_manager.db_execute_select(TEXT_FILTER_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_text_filter()
    count_after = database_manager.db_execute_select(TEXT_FILTER_COUNT)
    assert 1 == count_after[0][0]

    drop_table("TextFilter")
    create_old_text_filter()


@pytest.mark.asyncio()
async def test_remake_text_filter_moderation():
    drop_table("TextFilterModeration")
    create_old_text_filter_moderation()
    populate_old_text_filter_moderation()

    before_expected_result = [("1", 1), ("2", 1), ("3", 2), ("4", 2)]
    before_data_stored = database_manager.db_execute_select(TEXT_FILTER_MODERATION_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_text_filter_moderation()
    after_expected_result = [("1", "1"), ("2", "1"), ("3", "2"), ("4", "2")]
    after_data_stored = database_manager.db_execute_select(TEXT_FILTER_MODERATION_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("TextFilterModeration")
    create_old_text_filter_moderation()


@pytest.mark.asyncio()
async def test_remake_text_filter_moderation_no_table():
    drop_table("TextFilterModeration")

    count_before = database_manager.db_execute_select(TEXT_FILTER_MODERATION_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_text_filter_moderation()
    count_after = database_manager.db_execute_select(TEXT_FILTER_MODERATION_COUNT)
    assert 1 == count_after[0][0]

    drop_table("TextFilterModeration")
    create_old_text_filter_moderation()


@pytest.mark.asyncio()
async def test_remake_text_filter_ignore_list():
    drop_table("TextFilterIgnoreList")
    create_old_text_filter_ignore_list()
    populate_old_text_filter_ignore_list()

    before_expected_result = [("1", 1, "TYPE1", 1), ("2", 1, "TYPE2", 1), ("3", 2, "TYPE3", 1), ("4", 2, "TYPE4", 1)]
    before_data_stored = database_manager.db_execute_select(TEXT_FILTER_IGNORE_LIST_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_text_filter_ignore_list()
    after_expected_result = [("1", "1", "TYPE1", "1"), ("2", "1", "TYPE2", "1"), ("3", "2", "TYPE3", "1"),
                             ("4", "2", "TYPE4", "1")]
    after_data_stored = database_manager.db_execute_select(TEXT_FILTER_IGNORE_LIST_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("TextFilterIgnoreList")
    create_old_text_filter_ignore_list()


@pytest.mark.asyncio()
async def test_remake_text_filter_ignore_list_no_table():
    drop_table("TextFilterIgnoreList")

    count_before = database_manager.db_execute_select(TEXT_FILTER_IGNORE_LIST_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_text_filter_ignore_list()
    count_after = database_manager.db_execute_select(TEXT_FILTER_IGNORE_LIST_COUNT)
    assert 1 == count_after[0][0]

    drop_table("TextFilterIgnoreList")
    create_old_text_filter_ignore_list()


@pytest.mark.asyncio()
async def test_remake_guild_rfr_messages():
    drop_table("GuildRFRMessages")
    create_old_guild_rfr_messages()
    populate_old_guild_rfr_messages()

    before_expected_result = [(1, 1, 1, 1), (1, 2, 2, 2), (2, 3, 3, 3), (2, 3, 4, 4)]
    before_data_stored = database_manager.db_execute_select(GUILD_RFR_MESSAGES_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_guild_rfr_messages()
    after_expected_result = [("1", "1", "1", 1), ("1", "2", "2", 2), ("2", "3", "3", 3), ("2", "3", "4", 4)]
    after_data_stored = database_manager.db_execute_select(GUILD_RFR_MESSAGES_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("GuildRFRMessages")
    create_old_guild_rfr_messages()


@pytest.mark.asyncio()
async def test_remake_guild_rfr_messages_no_table():
    drop_table("GuildRFRMessages")

    count_before = database_manager.db_execute_select(GUILD_RFR_MESSAGES_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_guild_rfr_messages()
    count_after = database_manager.db_execute_select(GUILD_RFR_MESSAGES_COUNT)
    assert 1 == count_after[0][0]

    drop_table("GuildRFRMessages")
    create_old_guild_rfr_messages()


@pytest.mark.asyncio()
async def test_remake_rfr_message_emoji_roles():
    drop_table("RFRMessageEmojiRoles")
    create_old_rfr_message_emoji_roles()
    populate_old_rfr_message_emoji_roles()

    before_expected_result = [(1, "EMOJI1", 1), (2, "EMOJI2", 2), (3, "EMOJI3", 3), (4, "EMOJI4", 4)]
    before_data_stored = database_manager.db_execute_select(RFR_MESSAGE_EMOJI_ROLES_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_rfr_message_emoji_roles()
    after_expected_result = [(1, "EMOJI1", "1"), (2, "EMOJI2", "2"), (3, "EMOJI3", "3"), (4, "EMOJI4", "4")]
    after_data_stored = database_manager.db_execute_select(RFR_MESSAGE_EMOJI_ROLES_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("RFRMessageEmojiRoles")
    create_old_rfr_message_emoji_roles()


@pytest.mark.asyncio()
async def test_remake_rfr_message_emoji_roles_no_table():
    drop_table("RFRMessageEmojiRoles")

    count_before = database_manager.db_execute_select(RFR_MESSAGE_EMOJI_ROLES_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_rfr_message_emoji_roles()
    count_after = database_manager.db_execute_select(RFR_MESSAGE_EMOJI_ROLES_COUNT)
    assert 1 == count_after[0][0]

    drop_table("RFRMessageEmojiRoles")
    create_old_rfr_message_emoji_roles()


@pytest.mark.asyncio()
async def test_remake_guild_rfr_required_roles():
    drop_table("GuildRFRRequiredRoles")
    create_old_guild_rfr_required_roles()
    populate_old_guild_rfr_required_roles()

    before_expected_result = [(1, 1), (1, 2), (2, 3), (2, 4)]
    before_data_stored = database_manager.db_execute_select(GUILD_RFR_REQUIRED_ROLES_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_guild_rfr_required_roles()
    after_expected_result = [("1", "1"), ("1", "2"), ("2", "3"), ("2", "4")]
    after_data_stored = database_manager.db_execute_select(GUILD_RFR_REQUIRED_ROLES_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("GuildRFRRequiredRoles")
    create_old_guild_rfr_required_roles()


@pytest.mark.asyncio()
async def test_remake_guild_rfr_required_roles_no_table():
    drop_table("GuildRFRRequiredRoles")

    count_before = database_manager.db_execute_select(GUILD_RFR_REQUIRED_ROLES_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_guild_rfr_required_roles()
    count_after = database_manager.db_execute_select(GUILD_RFR_REQUIRED_ROLES_COUNT)
    assert 1 == count_after[0][0]

    drop_table("GuildRFRRequiredRoles")
    create_old_guild_rfr_required_roles()


@pytest.mark.asyncio()
async def test_remake_guild_colour_change_permissions():
    drop_table("GuildColourChangePermissions")
    create_old_guild_colour_change_permissions()
    populate_old_guild_colour_change_permissions()

    before_expected_result = [(1, 1), (1, 2), (2, 3), (2, 4)]
    before_data_stored = database_manager.db_execute_select(GUILD_COLOUR_CHANGE_PERMISSIONS_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_guild_colour_change_permissions()
    after_expected_result = [("1", 1), ("1", 2), ("2", 3), ("2", 4)]
    after_data_stored = database_manager.db_execute_select(GUILD_COLOUR_CHANGE_PERMISSIONS_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("GuildColourChangePermissions")
    create_old_guild_colour_change_permissions()


@pytest.mark.asyncio()
async def test_remake_guild_colour_change_permissions_no_table():
    drop_table("GuildColourChangePermissions")

    count_before = database_manager.db_execute_select(GUILD_COLOUR_CHANGE_PERMISSIONS_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_guild_colour_change_permissions()
    count_after = database_manager.db_execute_select(GUILD_COLOUR_CHANGE_PERMISSIONS_COUNT)
    assert 1 == count_after[0][0]

    drop_table("GuildColourChangePermissions")
    create_old_guild_colour_change_permissions()


@pytest.mark.asyncio()
async def test_remake_guild_invalid_custom_colour_roles():
    drop_table("GuildInvalidCustomColourRoles")
    create_old_guild_invalid_custom_colour_roles()
    populate_old_guild_invalid_custom_colour_roles()

    before_expected_result = [(1, 5), (1, 6), (2, 7), (2, 8)]
    before_data_stored = database_manager.db_execute_select(GUILD_INVALID_CUSTOM_COLOUR_ROLES_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_guild_invalid_custom_colour_roles()
    after_expected_result = [("1", 5), ("1", 6), ("2", 7), ("2", 8)]
    after_data_stored = database_manager.db_execute_select(GUILD_INVALID_CUSTOM_COLOUR_ROLES_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("GuildInvalidCustomColourRoles")
    create_old_guild_invalid_custom_colour_roles()


@pytest.mark.asyncio()
async def test_remake_guild_invalid_custom_colour_roles_no_table():
    drop_table("GuildInvalidCustomColourRoles")

    count_before = database_manager.db_execute_select(GUILD_INVALID_CUSTOM_COLOUR_ROLES_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_guild_invalid_custom_colour_roles()
    count_after = database_manager.db_execute_select(GUILD_INVALID_CUSTOM_COLOUR_ROLES_COUNT)
    assert 1 == count_after[0][0]

    drop_table("GuildInvalidCustomColourRoles")
    create_old_guild_invalid_custom_colour_roles()


@pytest.mark.asyncio()
async def test_remake_guild_usage():
    drop_table("GuildUsage")
    create_old_guild_usage()
    populate_old_guild_usage()

    before_expected_result = [(1, 1), (2, 2)]
    before_data_stored = database_manager.db_execute_select(GUILD_USAGE_SELECT)
    assert before_data_stored == before_expected_result
    migrate_database.remake_guild_usage()
    after_expected_result = [("1", "1"), ("2", "2")]
    after_data_stored = database_manager.db_execute_select(GUILD_USAGE_SELECT)
    assert after_data_stored == after_expected_result

    drop_table("GuildUsage")
    create_old_guild_usage()


@pytest.mark.asyncio()
async def test_remake_guild_usage_no_table():
    drop_table("GuildUsage")

    count_before = database_manager.db_execute_select(GUILD_USAGE_COUNT)
    assert 0 == count_before[0][0]
    migrate_database.remake_guild_usage()
    count_after = database_manager.db_execute_select(GUILD_USAGE_COUNT)
    assert 1 == count_after[0][0]

    drop_table("GuildUsage")
    create_old_guild_usage()


@pytest.mark.asyncio()
async def test_remake_guilds_no_guilds_no_extensions_table():
    drop_table("Guilds")
    drop_table("GuildExtensions")

    count_before_guilds = database_manager.db_execute_select(GUILDS_COUNT)
    assert 0 == count_before_guilds[0][0]
    count_before_extensions = database_manager.db_execute_select(GUILD_EXTENSION_COUNT)
    assert 0 == count_before_extensions[0][0]
    migrate_database.remake_guilds()
    count_after = database_manager.db_execute_select(GUILDS_COUNT)
    assert 1 == count_after[0][0]
    count_after_extensions = database_manager.db_execute_select(GUILD_EXTENSION_COUNT)
    assert 0 == count_after_extensions[0][0]

    drop_table("Guilds")


@pytest.mark.asyncio()
async def test_remake_guilds_only_no_guilds_table():
    drop_table("Guilds")
    create_old_guild_extensions()
    populate_old_guild_extensions()

    count_before_guilds = database_manager.db_execute_select(GUILDS_COUNT)
    assert 0 == count_before_guilds[0][0]
    count_before_extensions = database_manager.db_execute_select(GUILD_EXTENSION_COUNT)
    assert 1 == count_before_extensions[0][0]
    migrate_database.remake_guilds()
    migrate_database.remake_guild_extensions()
    count_after = database_manager.db_execute_select(GUILDS_COUNT)
    assert 1 == count_after[0][0]
    guild_extensions_guild_id = database_manager.db_execute_select("""SELECT guild_id FROM GuildExtensions""")
    guilds_guild_id = database_manager.db_execute_select("""SELECT guild_id FROM Guilds""")
    assert sorted(list(set(guild_extensions_guild_id))) == guilds_guild_id

    drop_table("Guilds")


@pytest.mark.asyncio()
async def test_remake_guilds_only_no_guild_extensions_table():
    create_guilds()
    populate_guilds()
    drop_table("GuildExtensions")

    count_before = database_manager.db_execute_select(GUILDS_COUNT)
    assert 1 == count_before[0][0]
    data_before = database_manager.db_execute_select(GUILDS_SELECT)
    migrate_database.remake_guilds()
    count_after = database_manager.db_execute_select(GUILDS_COUNT)
    assert 1 == count_after[0][0]
    data_after = database_manager.db_execute_select(GUILDS_SELECT)
    assert data_before == data_after

    drop_table("Guilds")


@pytest.mark.asyncio()
async def test_remake_guilds_both_exist_table():
    create_guilds()
    populate_guilds()
    create_old_guild_extensions()
    populate_old_guild_extensions()

    count_before_guilds = database_manager.db_execute_select(GUILDS_COUNT)
    assert 1 == count_before_guilds[0][0]
    count_before_guild_extension = database_manager.db_execute_select(GUILD_EXTENSION_COUNT)
    assert 1 == count_before_guild_extension[0][0]
    data_before = database_manager.db_execute_select(GUILDS_SELECT)
    migrate_database.remake_guilds()
    count_after_guilds = database_manager.db_execute_select(GUILDS_COUNT)
    assert 1 == count_after_guilds[0][0]
    count_after_guild_extension = database_manager.db_execute_select(GUILD_EXTENSION_COUNT)
    assert 1 == count_after_guild_extension[0][0]
    data_after = database_manager.db_execute_select(GUILDS_SELECT)
    assert data_before == data_after

    drop_table("Guilds")


@pytest.mark.asyncio()
async def test_get_largest_file_number():
    """
    Gets the largest number associated with a file in the database backups folder.
    First tests the folder is empty, creates 10 sequential files and tests the largest is gotten, finally creates 10 random files and tests largest is gotten.

    :return:
    """
    src = pathlib.Path(f'./KoalaDBBackups/')
    src.mkdir(exist_ok=True)
    recursively_delete_dir(src)
    assert migrate_database.get_largest_file_number() == 0
    src.mkdir()
    for i in range(0, 10):
        new_file = pathlib.Path(f'./KoalaDBBackups/backup_{i}')
        new_file.mkdir()
    assert migrate_database.get_largest_file_number() == 9
    recursively_delete_dir(src)
    src.mkdir()
    file_numbers = [0, 100]
    for i in range(0, 10):
        new_number = random.choice([x for x in range(max(file_numbers)) if x not in file_numbers])
        file_numbers.append(new_number)
        new_file = pathlib.Path(f'./KoalaDBBackups/backup_{new_number}')
        new_file.mkdir()
    assert migrate_database.get_largest_file_number() == sorted(file_numbers)[-2]
    src.mkdir(exist_ok=True)


@pytest.mark.asyncio()
async def test_backup_data():
    """
    Saves the current database to a test file, then compares the schema of the saved file against the original to ensure the schema copied across correctly.
    Next tests that the data in the two tables is copied across correctly.

    :return:
    """
    migrate_database.backup_data()
    db2 = pathlib.PurePath(f'KoalaDBBackups/backup_{migrate_database.get_largest_file_number()}/{database_manager.db_file_path}')

    conn, c = database_manager.create_connection_with_path(str(db2))

    expected = database_manager.db_execute_select("""select sql from sqlite_master where type = 'table'""")
    c.execute("""select sql from sqlite_master where type = 'table'""")
    saved_db_result = c.fetchall()
    assert expected == saved_db_result

    # Tests the data within the backup table is correct.
    table_names = database_manager.db_execute_select("SELECT name FROM sqlite_master WHERE type='table';")
    for table_name, in table_names:
        if table_name not in ["sqlite_master", "sqlite_sequence"]:
            assert database_manager.db_execute_select(f"pragma table_info('{table_name}')") == c.execute(
                f"pragma table_info('{table_name}')").fetchall()


@pytest.mark.asyncio()
async def test_rollback_database():
    """
    Tests broken database is saved correctly. Has similar tests to test_backup_data then tests the new table is properly linked.
    :return:
    """
    migrate_database.backup_data()
    drop_table("Guilds")
    drop_table("GuildExtensions")
    drop_table("TextFilter")
    migrate_database.rollback_database()

    broken_db_path = pathlib.Path() / 'KoalaDBBackups' / f'backup_{migrate_database.get_largest_file_number()}' / 'brokenKoalaDB.db'
    assert broken_db_path.is_file()

    db2 = pathlib.PurePath(f'KoalaDBBackups/backup_{migrate_database.get_largest_file_number()}/{database_manager.db_file_path}')

    conn, c = database_manager.create_connection_with_path(str(db2))

    expected = database_manager.db_execute_select("""select sql from sqlite_master where type = 'table'""")
    c.execute("""select sql from sqlite_master where type = 'table'""")
    saved_db_result = c.fetchall()
    assert expected == saved_db_result

    table_names = database_manager.db_execute_select("SELECT name FROM sqlite_master WHERE type='table';")
    for table_name, in table_names:
        if table_name not in ["sqlite_master", "sqlite_sequence"]:
            assert database_manager.db_execute_select(f"pragma table_info('{table_name}')") == c.execute(
                f"pragma table_info('{table_name}')").fetchall()

    conn.close()

    drop_table("Guilds")
    create_guilds()
    # testing database is linked properly
    guild_id_in_guilds_before = database_manager.db_execute_select("""SELECT guild_id FROM Guilds""")
    assert guild_id_in_guilds_before == []
    populate_guilds()
    guild_id_in_guilds_after = database_manager.db_execute_select("""SELECT guild_id FROM Guilds""")
    assert guild_id_in_guilds_after == [('1',), ('2',)]