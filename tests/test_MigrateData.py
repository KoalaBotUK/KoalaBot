import pytest

import KoalaBot
from utils.KoalaDBManager import KoalaDBManager
from utils.MigrateData import MigrateData

database_manager = KoalaDBManager(KoalaBot.DATABASE_PATH, KoalaBot.DB_KEY, KoalaBot.CONFIG_DIR)
database_manager.create_base_tables()
migrate_database = MigrateData(database_manager)

TABLE_NAME = "{TABLE_NAME}"
DROP_TABLE_SQL = f"DROP TABLE {TABLE_NAME}"


def create_base_tables():
    sql_create_koala_extensions_table = """
    CREATE TABLE IF NOT EXISTS KoalaExtensions (
    extension_id text NOT NULL PRIMARY KEY,
    subscription_required integer NOT NULL,
    available boolean NOT NULL,
    enabled boolean NOT NULL
    );"""

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

    sql_create_guild_welcome_messages_table = """
    CREATE TABLE IF NOT EXISTS GuildWelcomeMessages (
    guild_id integer NOT NULL PRIMARY KEY,
    welcome_message text
    );"""
    database_manager.db_execute_commit(sql_create_guild_welcome_messages_table)
    database_manager.db_execute_commit(sql_create_koala_extensions_table)
    database_manager.db_execute_commit(sql_create_guild_extensions_table)

    sql_create_usage_tables = """
            CREATE TABLE IF NOT EXISTS GuildUsage (
            guild_id integer NOT NULL,
            last_message_epoch_time integer NOT NULL,
            PRIMARY KEY (guild_id),
            FOREIGN KEY (guild_id) REFERENCES GuildExtensions(guild_id)
            );
            """
    database_manager.db_execute_commit(sql_create_usage_tables)

    sql_create_guild_colour_change_permissions_table = """
            CREATE TABLE IF NOT EXISTS GuildColourChangePermissions (
            guild_id integer NOT NULL,
            role_id integer NOT NULL,
            PRIMARY KEY (guild_id, role_id),
            FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
            );"""

    sql_create_guild_colour_change_invalid_colours_table = """
            CREATE TABLE IF NOT EXISTS GuildInvalidCustomColourRoles (
            guild_id integer NOT NULL,
            role_id integer NOT NULL,
            PRIMARY KEY (guild_id, role_id),
            FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
            );"""
    database_manager.db_execute_commit(sql_create_guild_colour_change_permissions_table)
    database_manager.db_execute_commit(sql_create_guild_colour_change_invalid_colours_table)

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

    sql_create_rfr_required_roles_table = """
            CREATE TABLE IF NOT EXISTS GuildRFRRequiredRoles (
            guild_id integer NOT NULL,
            role_id integer NOT NULL,
            PRIMARY KEY (guild_id, role_id),
            FOREIGN KEY (guild_id) REFERENCES GuildExtensions(guild_id),
            UNIQUE (guild_id, role_id)
            );
            """
    database_manager.db_execute_commit(sql_create_guild_rfr_message_ids_table)
    database_manager.db_execute_commit(sql_create_rfr_message_emoji_roles_table)
    database_manager.db_execute_commit(sql_create_rfr_required_roles_table)

    sql_create_text_filter_table = """
            CREATE TABLE IF NOT EXISTS TextFilter (
            filtered_text_id text NOT NULL,
            guild_id integer NOT NULL,
            filtered_text text NOT NULL,
            filter_type text NOT NULL,
            is_regex boolean NOT NULL,
            PRIMARY KEY (filtered_text_id)
            );"""

    sql_create_mod_table = """
            CREATE TABLE IF NOT EXISTS TextFilterModeration (
            channel_id text NOT NULL,
            guild_id integer NOT NULL,
            PRIMARY KEY (channel_id)
            );"""

    sql_create_ignore_list_table = """
            CREATE TABLE IF NOT EXISTS TextFilterIgnoreList (
            ignore_id text NOT NULL,
            guild_id integer NOT NULL,
            ignore_type text NOT NULL,
            ignore integer NOT NULL,
            PRIMARY KEY (ignore_id)
            );"""
    database_manager.db_execute_commit(sql_create_text_filter_table)
    database_manager.db_execute_commit(sql_create_mod_table)
    database_manager.db_execute_commit(sql_create_ignore_list_table)

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
    database_manager.db_execute_commit(sql_create_twitch_alerts_table)
    database_manager.db_execute_commit(sql_create_user_in_twitch_alert_table)
    database_manager.db_execute_commit(sql_create_team_in_twitch_alert_table)
    database_manager.db_execute_commit(sql_create_user_in_twitch_team_table)

    verified_table = """
            CREATE TABLE IF NOT EXISTS verified_emails (
            u_id integer NOT NULL,
            email text NOT NULL,
            PRIMARY KEY (u_id, email)
            );"""

    non_verified_table = """
            CREATE TABLE IF NOT EXISTS non_verified_emails (
            u_id integer NOT NULL,
            email text NOT NULL,
            token text NOT NULL,
            PRIMARY KEY (token)
            );"""

    role_table = """
            CREATE TABLE IF NOT EXISTS roles (
            s_id integer NOT NULL,
            r_id integer NOT NULL,
            email_suffix text NOT NULL,
            PRIMARY KEY (s_id, r_id, email_suffix),
            FOREIGN KEY (s_id) REFERENCES GuildExtensions (guild_id)
            );"""

    re_verify_table = """
            CREATE TABLE IF NOT EXISTS to_re_verify (
            u_id integer NOT NULL,
            r_id text NOT NULL,
            PRIMARY KEY (u_id, r_id)
            );"""
    database_manager.db_execute_commit(verified_table)
    database_manager.db_execute_commit(non_verified_table)
    database_manager.db_execute_commit(role_table)
    database_manager.db_execute_commit(re_verify_table)

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

    role_table = """
            CREATE TABLE IF NOT EXISTS VoteTargetRoles (
            vote_id integer NOT NULL,
            role_id integer NOT NULL
            );"""

    option_table = """
            CREATE TABLE IF NOT EXISTS VoteOptions (
            vote_id integer NOT NULL,
            opt_id integer NOT NULL,
            option_title text NOT NULL,
            option_desc text NOT NULL
            );"""

    delivered_table = """
            CREATE TABLE IF NOT EXISTS VoteSent (
            vote_id integer NOT NULL,
            vote_receiver_id integer NOT NULL,
            vote_receiver_message integer NOT NULL
            );"""
    database_manager.db_execute_commit(vote_table)
    database_manager.db_execute_commit(role_table)
    database_manager.db_execute_commit(option_table)
    database_manager.db_execute_commit(delivered_table)

    pass


def populate_tables():
    guild_extension_data = [(1, 1), (2, 1), (3, 1), (1, 2), (2, 2)]
    for i in guild_extension_data:
        database_manager.db_execute_commit('INSERT INTO GuildExtensions VALUES (?,?);', i)

    guilds_data = []
    #database_manager.db_execute_commit('INSERT INTO Guilds VALUES (?,?);', guild_extension_data)

    guild_welcome_messages_data = [(1, "This is a welcome message"), (2, "This is also a welcome message")]
    for i in guild_welcome_messages_data:
        database_manager.db_execute_commit('INSERT INTO GuildWelcomeMessages VALUES (?,?);', i)

    votes_data = [(1, 1, 1, "VOTE1", 1, 1, 0), (2, 1, 1, "VOTE2", 2, 2, 0), (3, 2, 2, "VOTE3", 3, 3, 0), (4, 2, 2, "VOTE4", 4, 4, 0)]
    for i in votes_data:
        database_manager.db_execute_commit('INSERT INTO Votes VALUES (?,?,?,?,?,?,?);', i)

    vote_sent_data = [(1, 5, "MESSAGE1"), (2, 6, "MESSAGE2"), (3, 7, "MESSAGE3"), (4, 8, "MESSAGE4")]
    for i in vote_sent_data:
        database_manager.db_execute_commit('INSERT INTO VoteSent VALUES (?,?,?);', i)

    vote_options_data = [(1, 1, "TITLE1", "DESCRIPTION1"), (2, 2, "TITLE2", "DESCRIPTION2"), (3, 3, "TITLE3", "DESCRIPTION3"), (4, 4, "TITLE4", "DESCRIPTION4")]
    for i in vote_options_data    :
        database_manager.db_execute_commit('INSERT INTO VoteOptions VALUES (?,?,?,?);', i)

    vote_target_roles_data = [(1, 1), (2, 2), (3, 3), (4, 4)]
    for i in vote_target_roles_data:
        database_manager.db_execute_commit('INSERT INTO VoteTargetRoles VALUES (?,?);', i)

    verified_emails_data = [(1, "EMAIL1"), (2, "EMAIL2"), (3, "EMAIL3"), (4, "EMAIL4")]
    for i in verified_emails_data:
        database_manager.db_execute_commit('INSERT INTO verified_emails VALUES (?,?);', i)

    not_verified_emails_data = [(5, "EMAIL5", "TOKEN5"), (6, "EMAIL6", "TOKEN6"), (7, "EMAIL7", "TOKEN7"), (8, "EMAIL8", "TOKEN8")]
    for i in not_verified_emails_data:
        database_manager.db_execute_commit('INSERT INTO non_verified_emails VALUES (?,?,?);', i)

    roles_data = [(1, 1, "EMAIL_SUFFIX1"), (1, 2, "EMAIL_SUFFIX2"), (2, 3, "EMAIL_SUFFIX3"), (2, 4, "EMAIL_SUFFIX4")]
    for i in roles_data:
        database_manager.db_execute_commit('INSERT INTO roles VALUES (?,?,?);', i)

    to_re_verify_data = [(1, 1), (2, 2)]
    for i in to_re_verify_data:
        database_manager.db_execute_commit('INSERT INTO to_re_verify VALUES (?,?);', i)

    twitch_alerts_data = [(1, 1, "MESSAGE1"), (1, 2, "MESSAGE2"), (2, 3, "MESSAGE3"), (2, 4, "MESSAGE4")]
    for i in twitch_alerts_data:
        database_manager.db_execute_commit('INSERT INTO TwitchAlerts VALUES (?,?,?);', i)

    user_in_twitch_alerts_data = [(1, "USERNAME1", "MESSAGE1", 1), (2, "USERNAME2", "MESSAGE2", 2), (3, "USERNAME3", "MESSAGE3", 3), (4, "USERNAME4", "MESSAGE4", 4)]
    for i in user_in_twitch_alerts_data:
        database_manager.db_execute_commit('INSERT INTO UserInTwitchAlert VALUES (?,?,?,?);', i)

    team_in_twitch_alerts_data = [(1, "TEAM_NAME1", "MESSAGE1"), (2, "TEAM_NAME2", "MESSAGE2"), (3, "TEAM_NAME3", "MESSAGE3"), (4, "TEAM_NAME4", "MESSAGE4")]
    for i in team_in_twitch_alerts_data:
        database_manager.db_execute_commit('INSERT INTO TeamInTwitchAlert (channel_id, twitch_team_name, custom_message) VALUES (?,?,?);', i)

    user_in_twitch_team_data = [(1, "USERNAME1", 1), (2, "USERNAME2", 2), (3, "USERNAME3", 3), (4, "USERNAME4", 4)]
    for i in user_in_twitch_team_data:
        database_manager.db_execute_commit('INSERT INTO UserInTwitchTeam VALUES (?,?,?);', i)

    text_filter_data = [(1, 1, "TEXT1", "TYPE1", True), (2, 1, "TEXT2", "TYPE2", False), (3, 2, "TEXT3", "TYPE3", True), (4, 2, "TEXT4", "TYPE4", False)]
    for i in text_filter_data:
        database_manager.db_execute_commit('INSERT INTO TextFilter VALUES (?,?,?,?,?);', i)

    text_filter_moderation_data = [(1, 1), (2, 1), (3, 2), (4, 2)]
    for i in text_filter_moderation_data:
        database_manager.db_execute_commit('INSERT INTO TextFilterModeration VALUES (?,?);', i)

    text_filter_ignore_list_data = [(1, 1, "TYPE1", 1), (2, 1, "TYPE2", 1), (3, 2, "TYPE3", 1), (4, 2, "TYPE4", 1)]
    for i in text_filter_ignore_list_data:
        database_manager.db_execute_commit('INSERT INTO TextFilterIgnoreList VALUES (?,?,?,?);', i)

    guild_rfr_messages_data = [(1, 1, 1, 1), (1, 2, 2, 2), (2, 3, 3, 3), (2, 3, 4, 4)]
    for i in guild_rfr_messages_data:
        database_manager.db_execute_commit('INSERT INTO GuildRFRMessages VALUES (?,?,?,?);', i)

    rfr_message_emoji_roles_data = [(1, "EMOJI1", 1), (2, "EMOJI2", 2), (3, "EMOJI3", 3), (4, "EMOJI4", 4)]
    for i in rfr_message_emoji_roles_data:
        database_manager.db_execute_commit('INSERT INTO RFRMessageEmojiRoles VALUES (?,?,?);', i)

    guild_rfr_required_roles_data = [(1, 1), (1, 2), (2, 3), (2, 4)]
    for i in guild_rfr_required_roles_data:
        database_manager.db_execute_commit('INSERT INTO GuildRFRRequiredRoles VALUES (?,?);', i)

    guild_colour_change_permissions_data = [(1, 1), (1, 2), (2, 3), (2, 4)]
    for i in guild_colour_change_permissions_data:
        database_manager.db_execute_commit('INSERT INTO GuildColourChangePermissions VALUES (?,?);', i)

    guild_invalid_custom_colour_roles_data = [(1, 5), (1, 6), (2, 7), (2, 8)]
    for i in guild_invalid_custom_colour_roles_data:
        database_manager.db_execute_commit('INSERT INTO GuildInvalidCustomColourRoles VALUES (?,?);', i)

    guild_usage_data = [(1, 1), (2, 2)]
    for i in guild_usage_data:
        database_manager.db_execute_commit('INSERT INTO GuildUsage VALUES (?,?);', i)


def drop_all_tables():
    table_names = database_manager.db_execute_select("SELECT name FROM sqlite_master WHERE type='table';")
    for table, in table_names:
        sql = DROP_TABLE_SQL.replace(TABLE_NAME, table)
        database_manager.db_execute_commit(sql)


@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    drop_all_tables()
    create_base_tables()
    populate_tables()
    yield
    drop_all_tables()


@pytest.mark.asyncio()
async def test_remake_guild_extensions():
    before_expected_result = [(1, 1), (2, 1), (3, 1), (1, 2), (2, 2)]
    before_data_stored = database_manager.db_execute_select("SELECT * FROM GuildExtensions")
    assert before_data_stored == before_expected_result
    migrate_database.remake_guild_extensions()
    after_expected_result = [('1', 1), ('2', 1), ('3', 1), ('1', 2), ('2', 2)]
    after_data_stored = database_manager.db_execute_select("SELECT * FROM GuildExtensions")


# async def test_remake_guilds_no_table():
#
#     pass