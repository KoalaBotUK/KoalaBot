import os
import shutil


def backup_data():
    """
    Stores the Koala.db database stored in the cwd to a new folder, new folder created each time in case of large rollback needed.
    :return:
    """
    try:
        size = len(os.listdir(os.getcwd() + '\\KoalaDBBackups'))
        if not os.path.exists('KoalaDBBackups\\backup_' + str(size)):
            os.makedirs('KoalaDBBackups\\backup_' + str(size))
        des = os.getcwd() + '\\KoalaDBBackups\\backup_' + str(size)
        src = os.path.join(os.getcwd(), 'Koala.db')
        shutil.copy(src, des)
        return True
    except Exception as e:
        print(e)
        return False


def reset_db():
    """
    Deletes an errored Koala.db database in the cwd and replaces it with the most recently saved database
    :return:
    """
    src = os.getcwd() + '\\KoalaDBBackups'
    last_db = src + '\\' + os.listdir(src)[-1] + '\\Koala.db'
    os.remove(os.getcwd() + '\\Koala.db')
    shutil.copy(last_db, os.getcwd())

class MigrateData:

    def __init__(self, database_manager):
        self.database_manager = database_manager

    def execute_update(self):
        """
        Sequentially applied the database update, if an error occurs then the entire database is rolled back.
        :return:
        """
        if backup_data():
            funcs = [self.remake_guilds, self.remake_guild_extensions, self.remake_guild_welcome_messages,
                     self.remake_votes, self.remake_vote_sent, self.remake_vote_options, self.remake_vote_target_roles,
                     self.remake_verified_emails, self.remake_not_verified_emails, self.remake_role_table,
                     self.remake_to_re_verify, self.remake_twitch_alerts, self.remake_user_in_twitch_alert,
                     self.remake_team_in_twitch_alert, self.remake_user_in_twitch_team, self.remake_text_filter,
                     self.remake_text_filter_moderation, self.remake_text_filter_ignore_list,
                     self.remake_guild_rf_messages, self.remake_rfr_message_emoji_roles,
                     self.remake_guild_rfr_required_roles, self.remake_guild_colour_change_permissions,
                     self.remake_guild_invalid_custom_colour_roles, self.remake_guild_usage]
            for func in funcs:
                try:
                    func()
                except Exception as e:
                    print(e)
                    reset_db()
                    break

    def remake_guilds(self):
        """
        Copies data from Guilds table if it doesn't exist, re-created the table with a given scheme, and inserts the
        data into the new table.
        :return:
        """
        sql_create_guilds_table = """
        CREATE TABLE IF NOT EXISTS Guilds (
        guild_id text NOT NULL,
        subscription integer NOT NULL DEFAULT 0,
        PRIMARY KEY (guild_id)
        );"""

        count_guilds = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='Guilds'""")
        count_guild_extension = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildExtensions'""")
        if not count_guilds[0][0] == count_guild_extension[0][0] == 0:
            if count_guilds[0][0] == 0:
                data = self.database_manager.db_execute_select("""SELECT guild_id FROM GuildExtensions;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS Guilds;""")
                self.database_manager.db_execute_commit(sql_create_guilds_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO  (guild_id, subscription) VALUES (?, ?);""",
                        args=[i, 0])
            else:
                data = self.database_manager.db_execute_select("""SELECT * FROM Guilds;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS Guilds;""")
                self.database_manager.db_execute_commit(sql_create_guilds_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO (guild_id, subscription) VALUES (?, ?);""",
                        args=list(i))

    def remake_guild_extensions(self):
        """
        Copies data from GuildExtensions table if it doesn't exist, re-created the table with a given scheme,
        and inserts the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildExtensions'""")
        if count[0][0] == 1:
            sql_create_guild_extensions_table = """
            CREATE TABLE IF NOT EXISTS GuildExtensions (
            extension_id text NOT NULL,
            guild_id text NOT NULL,
            PRIMARY KEY (extension_id,guild_id),
            CONSTRAINT fk_extensions
                FOREIGN KEY (extension_id) 
                REFERENCES KoalaExtensions (extension_id)
                ON DELETE CASCADE,
    
                FOREIGN KEY (guild_id)
                REFERENCES Guilds (guild_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM GuildExtensions;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS GuildExtensions;""")
            self.database_manager.db_execute_commit(sql_create_guild_extensions_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO GuildExtensions (extension_id, guild_id) VALUES (?, ?);""",
                    args=list(i))

    def remake_guild_welcome_messages(self):
        """
        Copies data from GuildWelcomeMessage table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildWelcomeMessages'""")
        if count[0][0] == 1:
            sql_create_guild_welcome_messages_table = """
            CREATE TABLE IF NOT EXISTS GuildWelcomeMessages (
            guild_id text NOT NULL PRIMARY KEY,
            welcome_message text,
            FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM GuildWelcomeMessages;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS GuildWelcomeMessages;""")
            self.database_manager.db_execute_commit(sql_create_guild_welcome_messages_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO GuildWelcomeMessages (guild_id, welcome_message) VALUES (?, ?);""",
                    args=list(i))

    def remake_votes(self):
        """
        Copies data from Votes table if it doesn't exist, re-created the table with a given scheme, and inserts the data
        into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='Votes'""")
        if count[0][0] == 1:
            vote_table = """
            CREATE TABLE IF NOT EXISTS Votes (
            vote_id text NOT NULL,
            author_id text NOT NULL,
            guild_id text NOT NULL,
            title text NOT NULL,
            chair_id text,
            voice_id text,
            end_time float,
            PRIMARY KEY (vote_id),
            FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM Votes;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS Votes;""")
            self.database_manager.db_execute_commit(vote_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO  (vote_id, author_id, guild_id, title, chair_id, voice_id, end_time) VALUES (?, ?, ?, ?, ?, ?, ?);""",
                    args=list(i))

    def remake_vote_sent(self):
        """
        Copies data from VoteSent table if it doesn't exist, re-created the table with a given scheme, and inserts the
        data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='VoteSent'""")
        if count[0][0] == 1:
            delivered_table = """
            CREATE TABLE IF NOT EXISTS VoteSent (
            vote_id text NOT NULL,
            vote_receiver_id text NOT NULL,
            vote_receiver_message text NOT NULL,
            PRIMARY KEY (vote_id),
            FOREIGN KEY (vote_id) REFERENCES Votes (vote_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM VoteSent;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS VoteSent;""")
            self.database_manager.db_execute_commit(delivered_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO VoteSent (vote_id, vote_receiver_id, vote_receiver_message) VALUES (?, ?, ?);""",
                    args=list(i))

    def remake_vote_options(self):
        """
        Copies data from VoteOptions table if it doesn't exist, re-created the table with a given scheme, and inserts
        the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='VoteOptions'""")
        if count[0][0] == 1:
            option_table = """
            CREATE TABLE IF NOT EXISTS VoteOptions (
            vote_id text NOT NULL,
            opt_id text NOT NULL,
            option_title text NOT NULL,
            option_desc text NOT NULL,
            PRIMARY KEY (vote_id),
            FOREIGN KEY (vote_id) REFERENCES Votes (vote_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM VoteOptions;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS VoteOptions;""")
            self.database_manager.db_execute_commit(option_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO VoteOptions (vote_id, opt_id, option_title, option_desc) VALUES (?, ?, ?, ?);""",
                    args=list(i))

    def remake_vote_target_roles(self):
        """
        Copies data from VoteTargetRoles table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='VoteTargetRoles'""")
        if count[0][0] == 1:
            role_table = """
            CREATE TABLE IF NOT EXISTS VoteTargetRoles (
            vote_id text NOT NULL,
            role_id text NOT NULL,
            PRIMARY KEY (vote_id),
            FOREIGN KEY (vote_id) REFERENCES Votes (vote_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM VoteTargetRoles;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS VoteTargetRoles;""")
            self.database_manager.db_execute_commit(role_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO VoteTargetRoles (vote_id, role_id) VALUES (?, ?);""",
                    args=list(i))

    def remake_verified_emails(self):
        """
        Copies data from VerifiedEmails table if it doesn't exist, re-created the table with a given scheme, and inserts
        the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='VerifiedEmails'""")
        if count[0][0] == 1:
            verified_table = """
            CREATE TABLE IF NOT EXISTS VerifiedEmails (
            user_id text NOT NULL,
            email text NOT NULL,
            PRIMARY KEY (user_id, email)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM VerifiedEmails;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS VerifiedEmails;""")
            self.database_manager.db_execute_commit(verified_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO VerifiedEmails (user_id, email) VALUES (?, ?);""",
                    args=list(i))

    def remake_not_verified_emails(self):
        """
        Copies data from NonVerifiedEmails table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='NonVerifiedEmails'""")
        if count[0][0] == 1:
            non_verified_table = """
            CREATE TABLE IF NOT EXISTS NonVerifiedEmails (
            user_id text NOT NULL,
            email text NOT NULL,
            token text NOT NULL,
            PRIMARY KEY (token)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM NonVerifiedEmails;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS NonVerifiedEmails;""")
            self.database_manager.db_execute_commit(non_verified_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO NonVerifiedEmails (user_id, email, token) VALUES (?, ?, ?);""",
                    args=list(i))

    def remake_role_table(self):
        """
        Copies data from Roles table if it doesn't exist, re-created the table with a given scheme, and inserts the data
        into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='Roles'""")
        if count[0][0] == 1:
            role_table = """
            CREATE TABLE IF NOT EXISTS Roles (
            guild_id text NOT NULL,
            role_id text NOT NULL,
            email_suffix text NOT NULL,
            PRIMARY KEY (guild_id, role_id, email_suffix),
            FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM Roles;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS Roles;""")
            self.database_manager.db_execute_commit(role_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO Roles (guild_id, role_id, email_suffix) VALUES (?, ?, ?);""",
                    args=list(i))

    def remake_to_re_verify(self):
        """
        Copies data from ToReVerify table if it doesn't exist, re-created the table with a given scheme, and inserts the
        data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='ToReVerify'""")
        if count[0][0] == 1:
            re_verify_table = """
            CREATE TABLE IF NOT EXISTS ToReVerify (
            user_id text NOT NULL,
            role_id text NOT NULL,
            PRIMARY KEY (user_id, role_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM ToReVerify;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS ToReVerify;""")
            self.database_manager.db_execute_commit(re_verify_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO ToReVerify (user_id, role_id) VALUES (?, ?);""",
                    args=list(i))

    def remake_twitch_alerts(self):
        """
        Copies data from TwitchAlerts table if it doesn't exist, re-created the table with a given scheme, and inserts
        the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TwitchAlerts'""")
        if count[0][0] == 1:
            sql_create_twitch_alerts_table = """
            CREATE TABLE IF NOT EXISTS TwitchAlerts (
            guild_id text NOT NULL,
            channel_id text NOT NULL,
            default_message text NOT NULL,
            PRIMARY KEY (guild_id, channel_id),
            CONSTRAINT fk_guild
                FOREIGN KEY (guild_id) 
                REFERENCES Guilds (guild_id)
                ON DELETE CASCADE 
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM TwitchAlerts;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS TwitchAlerts;""")
            self.database_manager.db_execute_commit(sql_create_twitch_alerts_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO TextTable (guild_id, channel_id, default_message) VALUES (?, ?, ?);""",
                    args=list(i))

    def remake_user_in_twitch_alert(self):
        """
        Copies data from UserInTwitchAlert table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='UserInTwitchAlert'""")
        if count[0][0] == 1:
            sql_create_user_in_twitch_alert_table = """
            CREATE TABLE IF NOT EXISTS UserInTwitchAlert (
            channel_id text NOT NULL,
            twitch_username text NOT NULL,
            custom_message text,
            message_id text,
            PRIMARY KEY (channel_id, twitch_username),
            CONSTRAINT fk_channel
                FOREIGN KEY (channel_id) 
                REFERENCES TwitchAlerts (channel_id)
                ON DELETE CASCADE 
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM UserInTwitchAlert;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS UserInTwitchAlert;""")
            self.database_manager.db_execute_commit(sql_create_user_in_twitch_alert_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO UserInTwitchAlert (chanel_id, twitch_username, custom_message, message_id) VALUES (?, ?, ? ,?);""",
                    args=list(i))

    def remake_team_in_twitch_alert(self):
        """
        Copies data from TeamInTwitchAlert table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TeamInTwitchAlert'""")
        if count[0][0] == 1:
            sql_create_team_in_twitch_alert_table = """
            CREATE TABLE IF NOT EXISTS TeamInTwitchAlert (
            team_twitch_alert_id integer PRIMARY KEY AUTOINCREMENT, 
            channel_id text NOT NULL,
            twitch_team_name text NOT NULL,
            custom_message text,
            CONSTRAINT fk_channel
                FOREIGN KEY (channel_id) 
                REFERENCES TwitchAlerts (channel_id)
                ON DELETE CASCADE 
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM TeamInTwitchAlert;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS TeamInTwitchAlert;""")
            self.database_manager.db_execute_commit(sql_create_team_in_twitch_alert_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO TeamInTwitchAlert (team_twitch_alert_id, channel_id, twitch_team_name, custom_message) VALUES (?, ?, ?, ?);""",
                    args=list(i))

    def remake_user_in_twitch_team(self):
        """
        Copies data from UserInTwitchTeam table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='UserInTwitchTeam'""")
        if count[0][0] == 1:
            sql_create_user_in_twitch_team_table = """
            CREATE TABLE IF NOT EXISTS UserInTwitchTeam (
            team_twitch_alert_id integer NOT NULL,
            twitch_username text NOT NULL,
            message_id text,
            PRIMARY KEY (team_twitch_alert_id, twitch_username),
            CONSTRAINT fk_twitch_team_alert
                FOREIGN KEY (team_twitch_alert_id) 
                REFERENCES TeamInTwitchAlert (team_twitch_alert_id)
                ON DELETE CASCADE 
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM UserInTwitchTeam;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS UserInTwitchTeam;""")
            self.database_manager.db_execute_commit(sql_create_user_in_twitch_team_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO UserInTwitchTeam (team_twitch_alert_id, twitch_username, meaage_id) VALUES (?, ?, ?);""",
                    args=list(i))

    def remake_text_filter(self):
        """
        Copies data from TextFilter table if it doesn't exist, re-created the table with a given scheme, and inserts the
        data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TextFilter'""")
        if count[0][0] == 1:
            sql_create_text_filter_table = """
            CREATE TABLE IF NOT EXISTS TextFilter (
            filtered_text_id text NOT NULL,
            guild_id text NOT NULL,
            filtered_text text NOT NULL,
            filter_type text NOT NULL,
            is_regex boolean NOT NULL,
            PRIMARY KEY (filtered_text_id),
            FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM TextFilter;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS TextFilter;""")
            self.database_manager.db_execute_commit(sql_create_text_filter_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO TextFilter (filtered_text_id, guild_id, filtered_text, filter_type, is_regex) VALUES (?, ?, ?, ?, ?);""",
                    args=list(i))

    def remake_text_filter_moderation(self):
        """
        Copies data from TextFilterModeration table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TextFilterModeration'""")
        if count[0][0] == 1:
            sql_create_mod_table = """
            CREATE TABLE IF NOT EXISTS TextFilterModeration (
            channel_id text NOT NULL,
            guild_id text NOT NULL,
            PRIMARY KEY (channel_id),
            FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM TextFilterModeration;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS TextFilterModeration;""")
            self.database_manager.db_execute_commit(sql_create_mod_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO TextFilterModeration (chanel_id, guild_id) VALUES (?, ?);""",
                    args=list(i))

    def remake_text_filter_ignore_list(self):
        """
        Copies data from TextFilterIgnoreList table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TextFilterIgnoreList'""")
        if count[0][0] == 1:
            sql_create_ignore_list_table = """
            CREATE TABLE IF NOT EXISTS TextFilterIgnoreList (
            ignore_id text NOT NULL,
            guild_id text NOT NULL,
            ignore_type text NOT NULL,
            ignore text NOT NULL,
            PRIMARY KEY (ignore_id),
            FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM TextFilterIgnoreList;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS TextFilterIgnoreList;""")
            self.database_manager.db_execute_commit(sql_create_ignore_list_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO TextFilterIgnoreList (ignore_id, guild_id, ignore_type, ignore) VALUES (?, ?, ?, ?);""",
                    args=list(i))

    def remake_guild_rf_messages(self):
        """
        Copies data from GuildRFRMessages table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildRFRMessages'""")
        if count[0][0] == 1:
            sql_create_guild_rfr_message_ids_table = """
            CREATE TABLE IF NOT EXISTS GuildRFRMessages (
            guild_id text NOT NULL,
            channel_id text NOT NULL,
            message_id text NOT NULL,
            emoji_role_id text,
            PRIMARY KEY (emoji_role_id),
            FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id),
            UNIQUE (guild_id, channel_id, message_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM GuildRFRMessages;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS GuildRFRMessages;""")
            self.database_manager.db_execute_commit(sql_create_guild_rfr_message_ids_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO GuildRFRMessages (guild_id, channel_id, message_id, emoji_role_id) VALUES (?, ?, ?, ?);""",
                    args=list(i))

    def remake_rfr_message_emoji_roles(self):
        """
        Copies data from RFRMessageEmojiRoles table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='RFRMessageEmojiRoles'""")
        if count[0][0] == 1:
            sql_create_rfr_message_emoji_roles_table = """
            CREATE TABLE IF NOT EXISTS RFRMessageEmojiRoles (
            emoji_role_id text NOT NULL,
            emoji_raw text NOT NULL,
            role_id text NOT NULL,
            PRIMARY KEY (emoji_role_id, emoji_raw, role_id),
            FOREIGN KEY (emoji_role_id) REFERENCES GuildRFRMessages(emoji_role_id),
            UNIQUE (emoji_role_id, emoji_raw),
            UNIQUE  (emoji_role_id, role_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM RFRMessageEmojiRoles;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS RFRMessageEmojiRoles;""")
            self.database_manager.db_execute_commit(sql_create_rfr_message_emoji_roles_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO RFRMessageEmojiRoles (emoji_role_id, emoji_raw, role_id) VALUES (?, ?, ?);""",
                    args=list(i))

    def remake_guild_rfr_required_roles(self):
        """
        Copies data from GuildRFRRequiredRoles table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildRFRRequiredRoles'""")
        if count[0][0] == 1:
            sql_create_rfr_required_roles_table = """
            CREATE TABLE IF NOT EXISTS GuildRFRRequiredRoles (
            guild_id text NOT NULL,
            role_id text NOT NULL,
            PRIMARY KEY (guild_id, role_id),
            FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id),
            UNIQUE (guild_id, role_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM GuildRFRRequiredRoles;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS GuildRFRRequiredRoles;""")
            self.database_manager.db_execute_commit(sql_create_rfr_required_roles_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO GuildRFRRequiredRoles (guild_id, role_id) VALUES (?, ?, ?);""",
                    args=list(i))

    def remake_guild_colour_change_permissions(self):
        """
        Copies data from GuildColourChangePermissions table if it doesn't exist, re-created the table with a given
        scheme, and inserts the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildColourChangePermissions'""")
        if count[0][0] == 1:
            sql_create_guild_colour_change_permissions_table = """
            CREATE TABLE IF NOT EXISTS GuildColourChangePermissions (
            guild_id text NOT NULL,
            role_id integer NOT NULL,
            PRIMARY KEY (guild_id, role_id),
            FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM GuildColourChangePermissions;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS GuildColourChangePermissions;""")
            self.database_manager.db_execute_commit(sql_create_guild_colour_change_permissions_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO GuildColourChangePermissions (guild_id, role_id) VALUES (?, ?);""",
                    args=list(i))

    def remake_guild_invalid_custom_colour_roles(self):
        """
        Copies data from GuildInvalidCustomColourRoles table if it doesn't exist, re-created the table with a given
        scheme, and inserts the data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildInvalidCustomColourRoles'""")
        if count[0][0] == 1:
            sql_create_guild_colour_change_invalid_colours_table = """
            CREATE TABLE IF NOT EXISTS GuildInvalidCustomColourRoles (
            guild_id text NOT NULL,
            role_id integer NOT NULL,
            PRIMARY KEY (guild_id, role_id),
            FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
            );"""

            data = self.database_manager.db_execute_select("""SELECT * FROM GuildInvalidCustomColourRoles;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS GuildInvalidCustomColourRoles;""")
            self.database_manager.db_execute_commit(sql_create_guild_colour_change_invalid_colours_table)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO GuildInvalidCustomColourRoles (guild_id, role_id) VALUES (?, ?);""",
                    args=list(i))

    def remake_guild_usage(self):
        """
        Copies data from GuildUsage table if it doesn't exist, re-created the table with a given scheme, and inserts the
        data into the new table.
        :return:
        """
        count = self.database_manager.db_execute_select(
            """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildUsage'""")
        if count[0][0] == 1:
            sql_create_usage_tables = """
            CREATE TABLE IF NOT EXISTS GuildUsage (
            guild_id text NOT NULL,
            last_message_epoch_time text NOT NULL,
            PRIMARY KEY (guild_id),
            FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
            );
            """

            data = self.database_manager.db_execute_select("""SELECT * FROM GuildUsage;""")
            self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS GuildUsage;""")
            self.database_manager.db_execute_commit(sql_create_usage_tables)
            for i in data:
                self.database_manager.db_execute_commit(
                    """INSERT INTO GuildUsage (guild_id, last_message_epoch_time) VALUES (?, ?);""",
                    args=list(i))
