#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import os
import time
import asyncio
import aiohttp
import concurrent.futures


# Libs
import discord
from discord.ext import commands
from dotenv import load_dotenv
import requests

# Own modules
import KoalaBot
import utils.KoalaUtils
from utils.KoalaDBManager import KoalaDBManager

# Constants
load_dotenv()
DEFAULT_MESSAGE = "{username} is live, come watch!, {stream_link}"
KOALA_GREEN = discord.Colour.from_rgb(0, 170, 110)
CLIENT_ID = os.environ['TWITCH_TOKEN']
TWITCH_SECRET = os.environ['TWITCH_SECRET']
params = (
    ('client_id', str(CLIENT_ID)),
    ('client_secret', str(TWITCH_SECRET)),
    ('grant_type', 'client_credentials'),
)

response = requests.post('https://id.twitch.tv/oauth2/token', data=params)
AUTHORIZATION = response.json().get('access_token')

HEADERS = {'Client-ID': CLIENT_ID, 'Authorization': 'Bearer '+AUTHORIZATION}

# Variables


class TwitchAlert(commands.Cog):
    """
        A discord.py cog for alerting when someone goes live on twitch
    """
    def __init__(self, bot):
        """
        Initialises local variables
        :param bot: The bot client for this cog
        """
        self.bot = bot
        KoalaBot.database_manager.insert_extension("TwitchAlert", 0, False, True)
        self.ta_database_manager = TwitchAlertDBManager(KoalaBot.database_manager)
        self.ta_database_manager.create_twitch_alert_tables()
        self.loop_thread = None

    @commands.command()
    @commands.check(KoalaBot.is_admin)
    async def create_twitch_alert(self, ctx, *args):
        if len(args) == 0:
            default_message = None
        else:
            default_message = " ".join(args)
        new_id = self.ta_database_manager.create_new_ta(ctx.message.guild.id, default_message)
        new_embed = discord.Embed(title="New Twitch Alert Created!", colour=KOALA_GREEN)
        new_embed.set_footer(text=f"Twitch Alert ID: {new_id}")
        await ctx.send(embed=new_embed)

    @commands.command()
    @commands.check(KoalaBot.is_admin)
    async def add_twitch_alert_to_channel(self, ctx, twitch_alert_id, channel_id):
        self.ta_database_manager.add_ta_to_channel(twitch_alert_id, channel_id)
        new_embed = discord.Embed(title="Added to channel", colour=KOALA_GREEN)
        new_embed.set_footer(text=f"Twitch Alert ID: {twitch_alert_id}")
        await ctx.send(embed=new_embed)

    @commands.command()
    @commands.check(KoalaBot.is_admin)
    async def add_user_to_twitch_alert(self, ctx, twitch_alert_id, twitch_username, *args):
        if args:
            custom_message = " ".join(args)
        else:
            custom_message = None
        self.ta_database_manager.add_user_twitch_alert(twitch_alert_id, twitch_username, custom_message)
        new_embed = discord.Embed(title="Added User to Twitch Alert", colour=KOALA_GREEN)
        new_embed.set_footer(text=f"Twitch Alert ID: {twitch_alert_id}")
        await ctx.send(embed=new_embed)

    @commands.Cog.listener()
    async def on_ready(self):
        self.start_loop()

    def start_loop(self):
        if self.loop_thread is None:
            self.loop_thread = asyncio.get_event_loop().create_task(self.ta_database_manager.loop_check_live(self.bot))
        else:
            raise Exception("Loop is already running!")
        pass


def get_streams_data(usernames):
    url = 'https://api.twitch.tv/helix/streams?'
    result = requests.get(url, headers=HEADERS, params={'user_login': usernames}).json().get("data")
    return result


def get_user_data(username):
    url = 'https://api.twitch.tv/helix/users?login='+username
    result = requests.get(url, headers=HEADERS).json().get("data")[0]
    return result


def get_game_data(game_id):
    url = 'https://api.twitch.tv/helix/games?id='+game_id
    result = requests.get(url, headers=HEADERS).json().get("data")[0]
    return result


class TwitchAlertDBManager:
    def __init__(self, database_manager: KoalaDBManager):
        self.database_manager = database_manager
        self.loop_thread = None

    def create_twitch_alert_tables(self):
        sql_create_twitch_alerts_table = """
        CREATE TABLE IF NOT EXISTS TwitchAlerts (
        twitch_alert_id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
        guild_id integer NOT NULL,
        default_message text NOT NULL,
        FOREIGN KEY (guild_id) REFERENCES GuildExtensions (guild_id)
        );"""

        sql_create_twitch_alert_in_channel_table = """
        CREATE TABLE IF NOT EXISTS TwitchAlertInChannel (
        twitch_alert_id integer NOT NULL,
        channel_id integer NOT NULL,
        PRIMARY KEY (twitch_alert_id, channel_id),
        FOREIGN KEY (twitch_alert_id) REFERENCES TwitchAlerts (twitch_alert_id)
        );"""

        sql_create_user_in_twitch_alert_table = """
        CREATE TABLE IF NOT EXISTS UserInTwitchAlert (
        twitch_alert_id integer NOT NULL,
        twitch_username text NOT NULL,
        custom_message text,
        message_id integer,
        PRIMARY KEY (twitch_alert_id, twitch_username),
        FOREIGN KEY (twitch_alert_id) REFERENCES TwitchAlerts (twitch_alert_id)
        );"""

        sql_create_team_in_twitch_alert_table = """
        CREATE TABLE IF NOT EXISTS TeamInTwitchAlert (
        twitch_alert_id integer NOT NULL,
        twitch_team_name text NOT NULL,
        custom_message text,
        PRIMARY KEY (twitch_alert_id, twitch_team_name),
        FOREIGN KEY (twitch_alert_id) REFERENCES TwitchAlerts (twitch_alert_id)
        );"""

        sql_create_user_in_twitch_team_table = """
        CREATE TABLE IF NOT EXISTS UserInTwitchTeam (
        twitch_team_name text NOT NULL,
        twitch_username text NOT NULL,
        message_id integer,
        PRIMARY KEY (twitch_team_name, twitch_username),        
        FOREIGN KEY (twitch_team_name) REFERENCES TeamInTwitchAlert (twitch_team_name)
        );"""

        sql_create_twitch_display_in_channel_table = """
        CREATE TABLE IF NOT EXISTS TwitchDisplayInChannel (
        twitch_alert_id integer NOT NULL,
        channel_id integer NOT NULL,
        message_id text NOT NULL,
        PRIMARY KEY (twitch_alert_id, channel_id),        
        FOREIGN KEY (twitch_alert_id) REFERENCES TwitchAlerts (twitch_alert_id)
        );"""

        self.database_manager.db_execute_commit(sql_create_twitch_alerts_table)
        self.database_manager.db_execute_commit(sql_create_twitch_alert_in_channel_table)
        self.database_manager.db_execute_commit(sql_create_user_in_twitch_alert_table)
        self.database_manager.db_execute_commit(sql_create_team_in_twitch_alert_table)
        self.database_manager.db_execute_commit(sql_create_user_in_twitch_team_table)
        self.database_manager.db_execute_commit(sql_create_twitch_display_in_channel_table)

    def create_new_ta(self, guild_id, default_message):
        sql_search = [-1]
        new_id = None
        while sql_search:
            new_id = utils.KoalaUtils.random_id()
            sql_get_new_ta_id = f"""SELECT twitch_alert_id FROM TwitchAlerts WHERE twitch_alert_id={new_id}"""
            sql_search = self.database_manager.db_execute_select(sql_get_new_ta_id)

        if default_message is None:
            default_message = DEFAULT_MESSAGE

        sql_insert_twitch_alert = f"""
        INSERT INTO TwitchAlerts(twitch_alert_id, guild_id, default_message) VALUES({new_id},{guild_id},'{default_message}')
        """
        self.database_manager.db_execute_commit(sql_insert_twitch_alert)
        return new_id

    def add_ta_to_channel(self, twitch_alert_id, channel_id):
        sql_insert_twitch_alert_channel = f"""
        INSERT INTO TwitchAlertInChannel(twitch_alert_id, channel_id) VALUES({twitch_alert_id},'{channel_id}')
        """
        self.database_manager.db_execute_commit(sql_insert_twitch_alert_channel)

    def add_user_twitch_alert(self, twitch_alert_id, twitch_username, custom_message):
        sql_insert_user_twitch_alert = f"""
        INSERT INTO UserInTwitchAlert(twitch_alert_id, twitch_username, custom_message) 
        VALUES({twitch_alert_id},'{str.lower(twitch_username)}', '{custom_message}')
        """
        self.database_manager.db_execute_commit(sql_insert_user_twitch_alert)



    def end_loop(self):
        if self.loop_thread is not None:
            self.loop_thread.exit()
        else:
            raise Exception("Loop is not running!")
        pass

    async def loop_check_live(self, bot):
        print("Twitch Alert Loop Started")
        while True:
            sql_find_users = """SELECT twitch_username FROM UserInTwitchAlert"""
            users = self.database_manager.db_execute_select(sql_find_users)
            usernames = []
            users_left = 100
            for user in users:
                usernames.append(user[0])
                users_left -= 1
                if users_left == 0 or users[-1] == user:
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        user_streams = await asyncio.get_event_loop().run_in_executor(pool, get_streams_data, usernames)
                    users_left = 100

                    # Deals with online streams
                    for user_result in user_streams:
                        if user_result.get('type') == "live":
                            current_username = str.lower(user_result.get("user_name"))
                            print(current_username+" is live")
                            usernames.remove(current_username)

                            sql_find_message_id = f"""
                            SELECT message_id 
                            FROM UserInTwitchAlert 
                            WHERE twitch_username = '{current_username}'"""

                            message_id = self.database_manager.db_execute_select(sql_find_message_id)[0]
                            # If no Alert is present
                            if message_id[0] is None:

                                sql_find_channel_id = f"""
                                SELECT TwitchAlertInChannel.twitch_alert_id, channel_id 
                                FROM TwitchAlertInChannel 
                                JOIN TwitchAlerts TA on TwitchAlertInChannel.twitch_alert_id = TA.twitch_alert_id 
                                JOIN UserInTwitchAlert UITA on TA.twitch_alert_id = UITA.twitch_alert_id 
                                WHERE UITA.twitch_username = '{current_username}'"""
                                results = self.database_manager.db_execute_select(sql_find_channel_id)

                                for result in results:
                                    channel = bot.get_channel(id=result[1])
                                    with concurrent.futures.ThreadPoolExecutor() as pool2:
                                        user_account = await asyncio.get_event_loop().run_in_executor(pool2, get_user_data, user_result.get("user_name"))
                                        game_details = await asyncio.get_event_loop().run_in_executor(pool2, get_game_data, user_result.get("game_id"))

                                    new_message = await channel.send(embed=self.create_live_embed(user_result, user_account, game_details))

                                    sql_update_message_id = f"""
                                    UPDATE UserInTwitchAlert 
                                    SET message_id = {new_message.id} 
                                    WHERE twitch_alert_id = {result[0]} 
                                        AND twitch_username = '{current_username}'"""
                                    self.database_manager.db_execute_commit(sql_update_message_id)

                    # Deals with remaining offline streams
                    sql_select_offline_streams_with_message_ids = f"""
                    SELECT TAIC.channel_id, message_id
                    FROM UserInTwitchAlert
                    JOIN TwitchAlerts TA on UserInTwitchAlert.twitch_alert_id = TA.twitch_alert_id
                    JOIN TwitchAlertInChannel TAIC on TA.twitch_alert_id = TAIC.twitch_alert_id
                    WHERE message_id NOT NULL 
                    AND twitch_username in ({','.join(['?']*len(usernames))})"""

                    results = self.database_manager.db_execute_select(sql_select_offline_streams_with_message_ids, usernames)
                    for result in results:
                        await (await bot.get_channel(result[0]).fetch_message(result[1])).delete()
                    sql_update_offline_streams = f"""
                    UPDATE UserInTwitchAlert
                    SET message_id = NULL
                    WHERE twitch_username in ({','.join(['?']*len(usernames))})"""
                    self.database_manager.db_execute_commit(sql_update_offline_streams, usernames)
            time.sleep(1)
        pass

    def create_live_embed(self, stream_info, user_info, game_info):
        embed = discord.Embed(colour=KOALA_GREEN)
        embed.title = "<:twitch:734024383957434489>  "+stream_info.get("user_name")+" is now streaming!"
        embed.description = "https://twitch.tv/"+str.lower(stream_info.get("user_name"))
        embed.add_field(name="Stream Title", value=stream_info.get("title"))
        embed.add_field(name="Playing", value=game_info.get("name"))
        url = user_info.get("profile_image_url")
        embed.set_thumbnail(url=url)
        return embed


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(TwitchAlert(bot))


if __name__ == '__main__':
    print()
