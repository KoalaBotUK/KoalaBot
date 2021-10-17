"""
Koala Bot database migration util
Craeted by: Kieran Allinson
"""

import pathlib
import shutil
import logging
import sys
from pathlib import Path





class MigrateData:

    def __init__(self, database_manager):
        """
        Initalises database manager
        :param database_manager: The database manager used in this instance.
        """
        self.database_manager = database_manager

    def get_largest_file_number(self):
        """
        Gets the largest number from a list of files, this way files can be deleted but the numbering of the files will
        still increase. Files are named as backup_X, so the most recent save would be saved under the largest value of X.
        :return: Single integer number of the largest file name.
        """
        src = pathlib.Path().cwd() / 'KoalaDBBackups'
        if not src.is_dir():
            return 0
        else:
            filenames = [x.__str__().split('\\')[-1] for x in list(src.glob('*'))]
            values = [int(i[7:]) for i in filenames]
            values.sort()
            return values[-1]

    def backup_data(self):
        """
        Stores the Koala.db database stored in the cwd to a new folder, new folder created each time in case of large rollback needed.
        :return:
        """
        try:
            file_name = "backup_" + str(self.get_largest_file_number() + 1)
            src = pathlib.Path().cwd() / 'KoalaDBBackups' / file_name
            if not src.is_dir():
                src.mkdir()
            shutil.copy(self.database_manager.db_file_path, src)
            return True
        except Exception as e:
            logging.warning(f"MigrateData: {e}")
            return False

    def rollback_database(self):
        """
        Saves a copy of the broken database, then replaces it with the most recent backup.
        :return:
        """
        recent_backup = pathlib.Path(f'./KoalaDBBackups/backup_{self.get_largest_file_number()}/{self.database_manager.db_file_path}')
        broken_db = pathlib.Path(f'./{self.database_manager.db_file_path}')
        broken_db.replace('brokenKoalaDB.db')
        shutil.copy(pathlib.Path(f'./brokenKoalaDB.db'), pathlib.Path(f'./KoalaDBBackups/backup_{self.get_largest_file_number()}'))
        pathlib.Path(f'./brokenKoalaDB.db').unlink()
        shutil.copy(recent_backup, pathlib.Path(f'.'))

    def execute_update(self):
        """
        Sequentially applied the database update, if an error occurs then the database is rolled back and the bot is killed with exit code 1.
        :return:
        """
        if self.backup_data():
            funcs = [self.remake_guilds, self.remake_guild_extensions, self.remake_guild_welcome_messages,
                     self.remake_votes, self.remake_vote_sent, self.remake_vote_options, self.remake_vote_target_roles,
                     self.remake_verified_emails, self.remake_not_verified_emails, self.remake_role_table,
                     self.remake_to_re_verify, self.remake_twitch_alerts, self.remake_user_in_twitch_alert,
                     self.remake_team_in_twitch_alert, self.remake_user_in_twitch_team, self.remake_text_filter,
                     self.remake_text_filter_moderation, self.remake_text_filter_ignore_list,
                     self.remake_guild_rfr_messages, self.remake_rfr_message_emoji_roles,
                     self.remake_guild_rfr_required_roles, self.remake_guild_colour_change_permissions,
                     self.remake_guild_invalid_custom_colour_roles, self.remake_guild_usage]
            for func in funcs:
                try:
                    func()
                except Exception as e:
                    logging.error(f"Error in MigrateDatabase: {e}")
                    self.rollback_database()
                    sys.exit(3)

    def remake_guilds(self):
        """
        Copies data from Guilds table if it doesn't exist, re-created the table with a given scheme, and inserts the
        data into the new table.
        :return:
        """
        try:
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
            if count_guilds[0][0] == count_guild_extension[0][0] == 0:
                self.database_manager.db_execute_commit(sql_create_guilds_table)
            elif count_guilds[0][0] == 0 and count_guild_extension[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT guild_id FROM GuildExtensions;""")
                self.database_manager.db_execute_commit(sql_create_guilds_table)
                for i, in sorted(list(set(data))):
                    self.database_manager.db_execute_commit(
                        """INSERT INTO Guilds (guild_id, subscription) VALUES (?, ?);""",
                        args=[i, 0])
            else:
                data = self.database_manager.db_execute_select("""SELECT * FROM Guilds;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS Guilds;""")
                self.database_manager.db_execute_commit(sql_create_guilds_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO Guilds (guild_id, subscription) VALUES (?, ?);""",
                        i)
        except Exception as e:
            raise Exception(f"Error in remake_guilds: {e}")

    def remake_guild_extensions(self):
        """
        Copies data from GuildExtensions table if it doesn't exist, re-created the table with a given scheme,
        and inserts the data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildExtensions'""")
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
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM GuildExtensions;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS GuildExtensions;""")
                self.database_manager.db_execute_commit(sql_create_guild_extensions_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO GuildExtensions (extension_id, guild_id) VALUES (?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(sql_create_guild_extensions_table)
        except Exception as e:
            raise Exception(f"Error in remake_guild_extensions: {e}")

    def remake_guild_welcome_messages(self):
        """
        Copies data from GuildWelcomeMessage table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildWelcomeMessages'""")
            sql_create_guild_welcome_messages_table = """
                        CREATE TABLE IF NOT EXISTS GuildWelcomeMessages (
                        guild_id text NOT NULL PRIMARY KEY,
                        welcome_message text,
                        FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
                        );"""
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM GuildWelcomeMessages;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS GuildWelcomeMessages;""")
                self.database_manager.db_execute_commit(sql_create_guild_welcome_messages_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO GuildWelcomeMessages (guild_id, welcome_message) VALUES (?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(sql_create_guild_welcome_messages_table)
        except Exception as e:
            raise Exception(f"Error in remake_guild_welcome_messages: {e}")

    def remake_votes(self):
        """
        Copies data from Votes table if it doesn't exist, re-created the table with a given scheme, and inserts the data
        into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='Votes'""")
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
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM Votes;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS Votes;""")
                self.database_manager.db_execute_commit(vote_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO Votes (vote_id, author_id, guild_id, title, chair_id, voice_id, end_time) VALUES (?, ?, ?, ?, ?, ?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(vote_table)
        except Exception as e:
            raise Exception(f"Error in remake_votes: {e}")

    def remake_vote_sent(self):
        """
        Copies data from VoteSent table if it doesn't exist, re-created the table with a given scheme, and inserts the
        data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='VoteSent'""")
            delivered_table = """
                        CREATE TABLE IF NOT EXISTS VoteSent (
                        vote_id text NOT NULL,
                        vote_receiver_id text NOT NULL,
                        vote_receiver_message text NOT NULL,
                        PRIMARY KEY (vote_id),
                        FOREIGN KEY (vote_id) REFERENCES Votes (vote_id)
                        );"""
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM VoteSent;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS VoteSent;""")
                self.database_manager.db_execute_commit(delivered_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO VoteSent (vote_id, vote_receiver_id, vote_receiver_message) VALUES (?, ?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(delivered_table)
        except Exception as e:
            raise Exception(f"Error in remake_vote_sent: {e}")

    def remake_vote_options(self):
        """
        Copies data from VoteOptions table if it doesn't exist, re-created the table with a given scheme, and inserts
        the data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='VoteOptions'""")
            option_table = """
                        CREATE TABLE IF NOT EXISTS VoteOptions (
                        vote_id text NOT NULL,
                        opt_id text NOT NULL,
                        option_title text NOT NULL,
                        option_desc text NOT NULL,
                        PRIMARY KEY (vote_id),
                        FOREIGN KEY (vote_id) REFERENCES Votes (vote_id)
                        );"""
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM VoteOptions;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS VoteOptions;""")
                self.database_manager.db_execute_commit(option_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO VoteOptions (vote_id, opt_id, option_title, option_desc) VALUES (?, ?, ?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(option_table)
        except Exception as e:
            raise Exception(f"Error in remake_vote_options: {e}")

    def remake_vote_target_roles(self):
        """
        Copies data from VoteTargetRoles table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='VoteTargetRoles'""")
            role_table = """
                        CREATE TABLE IF NOT EXISTS VoteTargetRoles (
                        vote_id text NOT NULL,
                        role_id text NOT NULL,
                        PRIMARY KEY (vote_id),
                        FOREIGN KEY (vote_id) REFERENCES Votes (vote_id)
                        );"""
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM VoteTargetRoles;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS VoteTargetRoles;""")
                self.database_manager.db_execute_commit(role_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO VoteTargetRoles (vote_id, role_id) VALUES (?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(role_table)
        except Exception as e:
            raise Exception(f"Error in remake_vote_target_roles: {e}")

    def remake_verified_emails(self):
        """
        Copies data from VerifiedEmails table if it doesn't exist, re-created the table with a given scheme, and inserts
        the data into the new table.
        :return:
        """
        try:
            count_old = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='verified_emails'""")
            count_new = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='VerifiedEmails'""")
            verified_table = """
                 CREATE TABLE IF NOT EXISTS VerifiedEmails (
                 user_id text NOT NULL,
                 email text NOT NULL,
                 PRIMARY KEY (user_id, email)
                 );"""
            if count_old[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM verified_emails;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS verified_emails;""")
                self.database_manager.db_execute_commit(verified_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO VerifiedEmails (user_id, email) VALUES (?, ?);""",
                        args=list(i))
            elif count_new[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM VerifiedEmails;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS VerifiedEmails;""")
                self.database_manager.db_execute_commit(verified_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO VerifiedEmails (user_id, email) VALUES (?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(verified_table)
        except Exception as e:
            raise Exception(f"Error in remake_verified_emails: {e}")

    def remake_not_verified_emails(self):
        """
        Copies data from NonVerifiedEmails table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        try:
            count_old = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='non_verified_emails'""")
            count_new = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='NonVerifiedEmails'""")
            non_verified_table = """
                 CREATE TABLE IF NOT EXISTS NonVerifiedEmails (
                 user_id text NOT NULL,
                 email text NOT NULL,
                 token text NOT NULL,
                 PRIMARY KEY (token)
                 );"""
            if count_old[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM non_verified_emails;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS non_verified_emails;""")
                self.database_manager.db_execute_commit(non_verified_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO NonVerifiedEmails (user_id, email, token) VALUES (?, ?, ?);""",
                        args=list(i))
            elif count_new[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM NonVerifiedEmails;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS NonVerifiedEmails;""")
                self.database_manager.db_execute_commit(non_verified_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO NonVerifiedEmails (user_id, email, token) VALUES (?, ?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(non_verified_table)
        except Exception as e:
            raise Exception(f"Error in remake_not_verified_emails: {e}")

    def remake_role_table(self):
        """
        Copies data from Roles table if it doesn't exist, re-created the table with a given scheme, and inserts the data
        into the new table.
        :return:
        """
        try:
            count_old = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='roles'""")
            count_new = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='Roles'""")
            role_table = """
            CREATE TABLE IF NOT EXISTS Roles (
            guild_id text NOT NULL,
            role_id text NOT NULL,
            email_suffix text NOT NULL,
            PRIMARY KEY (guild_id, role_id, email_suffix),
            FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
            );"""
            if count_old[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM roles;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS roles;""")
                self.database_manager.db_execute_commit(role_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO Roles (guild_id, role_id, email_suffix) VALUES (?, ?, ?);""",
                        args=list(i))
            elif count_new[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM Roles;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS Roles;""")
                self.database_manager.db_execute_commit(role_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO Roles (guild_id, role_id, email_suffix) VALUES (?, ?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(role_table)
        except Exception as e:
            raise Exception(f"Error in remake_role_table: {e}")

    def remake_to_re_verify(self):
        """
        Copies data from ToReVerify table if it doesn't exist, re-created the table with a given scheme, and inserts the
        data into the new table.
        :return:
        """
        try:
            count_old = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='to_re_verify'""")
            count_new = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='ToReVerify'""")
            re_verify_table = """
                CREATE TABLE IF NOT EXISTS ToReVerify (
                user_id text NOT NULL,
                role_id text NOT NULL,
                PRIMARY KEY (user_id, role_id)
                );"""
            if count_old[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM to_re_verify;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS to_re_verify;""")
                self.database_manager.db_execute_commit(re_verify_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO ToReVerify (user_id, role_id) VALUES (?, ?);""",
                        args=list(i))
            if count_new[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM ToReVerify;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS ToReVerify;""")
                self.database_manager.db_execute_commit(re_verify_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO ToReVerify (user_id, role_id) VALUES (?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(re_verify_table)
        except Exception as e:
            raise Exception(f"Error in remake_to_re_verify: {e}")

    def remake_twitch_alerts(self):
        """
        Copies data from TwitchAlerts table if it doesn't exist, re-created the table with a given scheme, and inserts
        the data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TwitchAlerts'""")
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
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM TwitchAlerts;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS TwitchAlerts;""")
                self.database_manager.db_execute_commit(sql_create_twitch_alerts_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO TwitchAlerts (guild_id, channel_id, default_message) VALUES (?, ?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(sql_create_twitch_alerts_table)
        except Exception as e:
            raise Exception(f"Error in remake_twitch_alerts: {e}")

    def remake_user_in_twitch_alert(self):
        """
        Copies data from UserInTwitchAlert table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='UserInTwitchAlert'""")
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
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM UserInTwitchAlert;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS UserInTwitchAlert;""")
                self.database_manager.db_execute_commit(sql_create_user_in_twitch_alert_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO UserInTwitchAlert (channel_id, twitch_username, custom_message, message_id) VALUES (?, ?, ? ,?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(sql_create_user_in_twitch_alert_table)
        except Exception as e:
            raise Exception(f"Error in remake_user_in_twitch_alert: {e}")

    def remake_team_in_twitch_alert(self):
        """
        Copies data from TeamInTwitchAlert table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TeamInTwitchAlert'""")
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
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM TeamInTwitchAlert;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS TeamInTwitchAlert;""")
                self.database_manager.db_execute_commit(sql_create_team_in_twitch_alert_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO TeamInTwitchAlert (team_twitch_alert_id, channel_id, twitch_team_name, custom_message) VALUES (?, ?, ?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(sql_create_team_in_twitch_alert_table)
        except Exception as e:
            raise Exception(f"Error in remake_team_in_twitch_alert: {e}")

    def remake_user_in_twitch_team(self):
        """
        Copies data from UserInTwitchTeam table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='UserInTwitchTeam'""")
            sql_create_user_in_twitch_team_table = """
                CREATE TABLE IF NOT EXISTS UserInTwitchTeam (
                team_twitch_alert_id text NOT NULL,
                twitch_username text NOT NULL,
                message_id text,
                PRIMARY KEY (team_twitch_alert_id, twitch_username),
                CONSTRAINT fk_twitch_team_alert
                    FOREIGN KEY (team_twitch_alert_id) 
                    REFERENCES TeamInTwitchAlert (team_twitch_alert_id)
                    ON DELETE CASCADE 
                );"""
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM UserInTwitchTeam;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS UserInTwitchTeam;""")
                self.database_manager.db_execute_commit(sql_create_user_in_twitch_team_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO UserInTwitchTeam (team_twitch_alert_id, twitch_username, message_id) VALUES (?, ?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(sql_create_user_in_twitch_team_table)
        except Exception as e:
            raise Exception(f"Error in remake_user_in_twitch_team: {e}")

    def remake_text_filter(self):
        """
        Copies data from TextFilter table if it doesn't exist, re-created the table with a given scheme, and inserts the
        data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TextFilter'""")
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
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM TextFilter;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS TextFilter;""")
                self.database_manager.db_execute_commit(sql_create_text_filter_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO TextFilter (filtered_text_id, guild_id, filtered_text, filter_type, is_regex) VALUES (?, ?, ?, ?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(sql_create_text_filter_table)
        except Exception as e:
            raise Exception(f"Error in remake_text_filter: {e}")

    def remake_text_filter_moderation(self):
        """
        Copies data from TextFilterModeration table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TextFilterModeration'""")
            sql_create_mod_table = """
                       CREATE TABLE IF NOT EXISTS TextFilterModeration (
                       channel_id text NOT NULL,
                       guild_id text NOT NULL,
                       PRIMARY KEY (channel_id),
                       FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
                       );"""
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM TextFilterModeration;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS TextFilterModeration;""")
                self.database_manager.db_execute_commit(sql_create_mod_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO TextFilterModeration (channel_id, guild_id) VALUES (?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(sql_create_mod_table)
        except Exception as e:
            raise Exception(f"Error in remake_text_filter_moderation: {e}")

    def remake_text_filter_ignore_list(self):
        """
        Copies data from TextFilterIgnoreList table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TextFilterIgnoreList'""")
            sql_create_ignore_list_table = """
              CREATE TABLE IF NOT EXISTS TextFilterIgnoreList (
              ignore_id text NOT NULL,
              guild_id text NOT NULL,
              ignore_type text NOT NULL,
              ignore text NOT NULL,
              PRIMARY KEY (ignore_id),
              FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
              );"""
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM TextFilterIgnoreList;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS TextFilterIgnoreList;""")
                self.database_manager.db_execute_commit(sql_create_ignore_list_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO TextFilterIgnoreList (ignore_id, guild_id, ignore_type, ignore) VALUES (?, ?, ?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(sql_create_ignore_list_table)
        except Exception as e:
            raise Exception(f"Error in remake_text_filter_ignore_list: {e}")

    def remake_guild_rfr_messages(self):
        """
        Copies data from GuildRFRMessages table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildRFRMessages'""")
            sql_create_guild_rfr_message_ids_table = """
                 CREATE TABLE IF NOT EXISTS GuildRFRMessages (
                 guild_id text NOT NULL,
                 channel_id text NOT NULL,
                 message_id text NOT NULL,
                 emoji_role_id integer,
                 PRIMARY KEY (emoji_role_id),
                 FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id),
                 UNIQUE (guild_id, channel_id, message_id)
                 );"""
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM GuildRFRMessages;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS GuildRFRMessages;""")
                self.database_manager.db_execute_commit(sql_create_guild_rfr_message_ids_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO GuildRFRMessages (guild_id, channel_id, message_id, emoji_role_id) VALUES (?, ?, ?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(sql_create_guild_rfr_message_ids_table)
        except Exception as e:
            raise Exception(f"Error in remake_guild_rfr_messages: {e}")

    def remake_rfr_message_emoji_roles(self):
        """
        Copies data from RFRMessageEmojiRoles table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='RFRMessageEmojiRoles'""")
            sql_create_rfr_message_emoji_roles_table = """
                 CREATE TABLE IF NOT EXISTS RFRMessageEmojiRoles (
                 emoji_role_id integer NOT NULL,
                 emoji_raw text NOT NULL,
                 role_id text NOT NULL,
                 PRIMARY KEY (emoji_role_id, emoji_raw, role_id),
                 FOREIGN KEY (emoji_role_id) REFERENCES GuildRFRMessages(emoji_role_id),
                 UNIQUE (emoji_role_id, emoji_raw),
                 UNIQUE  (emoji_role_id, role_id)
                 );"""
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM RFRMessageEmojiRoles;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS RFRMessageEmojiRoles;""")
                self.database_manager.db_execute_commit(sql_create_rfr_message_emoji_roles_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO RFRMessageEmojiRoles (emoji_role_id, emoji_raw, role_id) VALUES (?, ?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(sql_create_rfr_message_emoji_roles_table)
        except Exception as e:
            raise Exception(f"Error in remake_rfr_message_emoji_roles: {e}")

    def remake_guild_rfr_required_roles(self):
        """
        Copies data from GuildRFRRequiredRoles table if it doesn't exist, re-created the table with a given scheme, and
        inserts the data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildRFRRequiredRoles'""")
            sql_create_rfr_required_roles_table = """
              CREATE TABLE IF NOT EXISTS GuildRFRRequiredRoles (
              guild_id text NOT NULL,
              role_id text NOT NULL,
              PRIMARY KEY (guild_id, role_id),
              FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id),
              UNIQUE (guild_id, role_id)
              );"""
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM GuildRFRRequiredRoles;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS GuildRFRRequiredRoles;""")
                self.database_manager.db_execute_commit(sql_create_rfr_required_roles_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO GuildRFRRequiredRoles (guild_id, role_id) VALUES (?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(sql_create_rfr_required_roles_table)
        except Exception as e:
            raise Exception(f"Error in remake_guild_rfr_required_roles: {e}")

    def remake_guild_colour_change_permissions(self):
        """
        Copies data from GuildColourChangePermissions table if it doesn't exist, re-created the table with a given
        scheme, and inserts the data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildColourChangePermissions'""")
            sql_create_guild_colour_change_permissions_table = """
                        CREATE TABLE IF NOT EXISTS GuildColourChangePermissions (
                        guild_id text NOT NULL,
                        role_id integer NOT NULL,
                        PRIMARY KEY (guild_id, role_id),
                        FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
                        );"""
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM GuildColourChangePermissions;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS GuildColourChangePermissions;""")
                self.database_manager.db_execute_commit(sql_create_guild_colour_change_permissions_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO GuildColourChangePermissions (guild_id, role_id) VALUES (?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(sql_create_guild_colour_change_permissions_table)
        except Exception as e:
            raise Exception(f"Error in remake_guild_colour_change_permissions: {e}")

    def remake_guild_invalid_custom_colour_roles(self):
        """
        Copies data from GuildInvalidCustomColourRoles table if it doesn't exist, re-created the table with a given
        scheme, and inserts the data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildInvalidCustomColourRoles'""")
            sql_create_guild_colour_change_invalid_colours_table = """
                 CREATE TABLE IF NOT EXISTS GuildInvalidCustomColourRoles (
                 guild_id text NOT NULL,
                 role_id integer NOT NULL,
                 PRIMARY KEY (guild_id, role_id),
                 FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
                 );"""
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM GuildInvalidCustomColourRoles;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS GuildInvalidCustomColourRoles;""")
                self.database_manager.db_execute_commit(sql_create_guild_colour_change_invalid_colours_table)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO GuildInvalidCustomColourRoles (guild_id, role_id) VALUES (?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(sql_create_guild_colour_change_invalid_colours_table)
        except Exception as e:
            raise Exception(f"Error in remake_guild_invalid_custom_colour_roles: {e}")

    def remake_guild_usage(self):
        """
        Copies data from GuildUsage table if it doesn't exist, re-created the table with a given scheme, and inserts the
        data into the new table.
        :return:
        """
        try:
            count = self.database_manager.db_execute_select(
                """SELECT count(name) FROM sqlite_master WHERE type='table' AND name='GuildUsage'""")
            sql_create_usage_tables = """
            CREATE TABLE IF NOT EXISTS GuildUsage (
            guild_id text NOT NULL,
            last_message_epoch_time text NOT NULL,
            PRIMARY KEY (guild_id),
            FOREIGN KEY (guild_id) REFERENCES Guilds (guild_id)
            );
            """
            if count[0][0] == 1:
                data = self.database_manager.db_execute_select("""SELECT * FROM GuildUsage;""")
                self.database_manager.db_execute_commit("""DROP TABLE IF EXISTS GuildUsage;""")
                self.database_manager.db_execute_commit(sql_create_usage_tables)
                for i in data:
                    self.database_manager.db_execute_commit(
                        """INSERT INTO GuildUsage (guild_id, last_message_epoch_time) VALUES (?, ?);""",
                        args=list(i))
            else:
                self.database_manager.db_execute_commit(sql_create_usage_tables)
        except Exception as e:
            raise Exception(f"Error in remake_guild_usage: {e}")
