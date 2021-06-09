#!/usr/bin/env python

"""
Koala Bot Cog providing Social Feed updates

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

import os
import time
import asyncio
import concurrent.futures
import logging

# Libs
import discord
import facebook
import tweepy
from discord.ext import commands
from dotenv import load_dotenv
from tweepy import StreamListener
import requests

# Own modules
import KoalaBot
from utils import KoalaDBManager
from utils.KoalaColours import *
from utils.KoalaUtils import extract_id, error_embed, is_channel_in_guild

# Constants
load_dotenv()
TWITTER_CLIENT_ID = os.environ['TWITTER_CLIENT_ID']
TWITTER_CLIENT_SECRET = os.environ['TWITTER_CLIENT_SECRET']
TWITTER_ACCESS_TOKEN = os.environ['TWITTER_ACCESS_TOKEN']
TWITTER_TOKEN_SECRET = os.environ['TWITTER_TOKEN_SECRET']


# Variables

def social_is_enabled(ctx):
    """
    A command used to check if the guild has enabled social alert
    e.g. @commands.check(KoalaBot.is_admin)
    :param ctx: The context of the message
    :return: True if admin or test, False otherwise
    """
    try:
        result = KoalaBot.check_guild_has_ext(ctx, "SocialAlert")
    except PermissionError:
        result = False

    return result or (str(ctx.author) == KoalaBot.TEST_USER and KoalaBot.is_dpytest)


class SocialAlert(commands.Cog):
    """
        A discord.py cog for providing social feed updates from Facebook, Instagram and Twitter
    """

    def __init__(self, bot, database_manager=None):
        if not database_manager:
            database_manager = KoalaBot.database_manager
        self.bot = bot
        database_manager.create_base_tables()
        database_manager.insert_extension("SocialAlert", 0, True, True)
        self.sa_database_manager = SocialAlertDBManager(database_manager, bot)
        self.sa_database_manager.create_tables()
        self.twitter_handler = TwitterAPIHandler(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET,
                                                 TWITTER_ACCESS_TOKEN, TWITTER_TOKEN_SECRET)

    # TODO: Extracting twitter display name from id and vice versa
    @commands.command(name="twitterAdd", aliases=['add_user_to_twitter_alert'])
    @commands.check(KoalaBot.is_admin)
    @commands.check(social_is_enabled)
    async def add_user_to_twitter_alert(self, ctx, raw_channel_id, twitter_id=None):
        """

        :param twitter_id:
        :param ctx:
        :param raw_channel_id:
        :param twitter_id:
        :return:
        """

        try:
            channel_id = extract_id(raw_channel_id)
        except TypeError:
            twitter_id = raw_channel_id
            channel_id = ctx.message.channel.id
        if twitter_id is None:
            raise commands.MissingRequiredArgument("twitter_id is a required argument that is missing.")

        # Check the channel specified is in this guild
        if not is_channel_in_guild(self.bot, ctx.message.guild.id, channel_id):
            await ctx.send(embed=error_embed("The channel ID provided is either invalid, or not in this server."))
            return

        self.twitter_handler.followed_accounts.append(twitter_id)

        default_message = "..."

        # Response Message
        new_embed = discord.Embed(title="Added User to Twitter Alert", colour=KOALA_GREEN,
                                  description=f"Channel: {channel_id}\n"
                                              f"User: {twitter_id}\n"
                                              f"Message: {default_message}")

        await ctx.send(embed=new_embed)

    @commands.command(name="twitterRemove", aliases=['remove_user_from_twitter_alert'])
    @commands.check(KoalaBot.is_admin)
    @commands.check(social_is_enabled)
    async def remove_user_from_twitter_alert(self, ctx, raw_channel_id, twitter_id=None):
        """

        :param ctx:
        :param raw_channel_id:
        :param twitter_id:
        :return:
        """

        try:
            channel_id = extract_id(raw_channel_id)
        except TypeError:
            twitch_username = raw_channel_id
            channel_id = ctx.message.channel.id
        if twitter_id is None:
            raise commands.MissingRequiredArgument("twitch_username is a required argument that is missing.")

        # Check the channel specified is in this guild
        if not is_channel_in_guild(self.bot, ctx.message.guild.id, channel_id):
            await ctx.send(embed=error_embed("The channel ID provided is either invalid, or not in this server."))
            return

        self.twitter_handler.followed_accounts.remove(twitter_id)

        # Response Message
        new_embed = discord.Embed(title="Removed User from Twitter Alert", colour=KOALA_GREEN,
                                  description=f"Channel: {channel_id}\n"
                                              f"User: {twitter_id}\n")

        await ctx.send(embed=new_embed)

    @commands.Cog.listener()
    async def on_ready(self):
        """

        :return:
        """
        self.post_tweets()

    def post_tweets(self):
        # Authenticate to Twitter
        auth = tweepy.OAuthHandler(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET)
        auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_TOKEN_SECRET)
        api = tweepy.API(auth)
        # test authentication
        try:
            api.verify_credentials()
            print("twitter authenticated")

            return discord.Embed(title=str(type("yeet").__name__), description=str("yeet"), colour=ERROR_RED)
        except:
            print("Error during authentication")

        # tweet_stream = tweepy.Stream(auth=self.twitter_handler.api, listener=self.twitter_handler.stream_listener)
        # current_text = tweet_stream.filter(follow=self.twitter_handler.followed_accounts, is_async=True)
        # tweet_embed = create_social_embed("twitter", "template_user", current_text)
        # channel = self.bot.get_channel("channel_id")
        # channel.send(embed=tweet_embed)


def create_social_embed(platform, user_info, post_info):
    """
    Creates an embed for social notifications
    :param platform: Social platform
    :param user_info: User information from API calls
    :param post_info: Post information from API calls
    :return: Created embed
    """
    embed = discord.Embed
    embed.title = platform + "New post from" + user_info

    embed.description = post_info
    # TODO:Make it more fancy with icons etc

    return embed


class TwitterAPIHandler:
    """
    A wrapper to interact with the Twitter Streaming API
    """

    def __init__(self, client_id: str, client_secret: str, access_token: str, token_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.token_secret = token_secret
        self.api = self.authenticate()
        self.stream_listener = TweetStreamListener()
        self.followed_accounts = []

    def authenticate(self):
        """
        Authenticates with Twitter using the tweepy handler
        :return: Twitter API object
        """
        auth = tweepy.OAuthHandler(self.client_id, self.client_secret)
        auth.set_access_token(self.access_token, self.token_secret)
        return tweepy.API(auth)


class TweetStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        return status.text

    def on_error(self, status_code):
        if status_code == 420:
            # Stops the stream
            return False


class SocialAlertDBManager:
    """
        A class for interacting with the Koala twitch database
        """

    def __init__(self, database_manager: KoalaDBManager, bot_client: discord.client):
        """
        Initialises local variables
        :param database_manager:
        :param bot_client:
        """
        self.database_manager = database_manager
        # self.twitch_handler = TwitterAPIHandler(TWITCH_CLIENT_ID, TWITCH_SECRET)
        self.bot = bot_client

    def get_parent_database_manager(self):
        """
        A getter for the database manager of this object
        :return:
        """
        return self.database_manager

    def create_tables(self):
        """
        Creates all the tables associated with the twitch alert extension
        :return:
        """

        # TwitchAlerts
        sql_create_social_alerts_table = """
           CREATE TABLE IF NOT EXISTS SocialAlerts (
           guild_id integer NOT NULL,
           channel_id integer NOT NULL,
           default_message text NOT NULL,
           PRIMARY KEY (guild_id, channel_id),
           CONSTRAINT fk_guild
               FOREIGN KEY (guild_id) 
               REFERENCES GuildExtensions (guild_id)
               ON DELETE CASCADE 
           );"""

        # UserInTwitterAlert
        sql_create_user_in_social_alert_table = """
           CREATE TABLE IF NOT EXISTS UserInSocialAlert (
           channel_id integer NOT NULL,
           twitter_username text NOT NULL,
           custom_message text,
           message_id integer,
           PRIMARY KEY (channel_id, twitter_username),
           CONSTRAINT fk_channel
               FOREIGN KEY (channel_id) 
               REFERENCES SocialAlerts (channel_id)
               ON DELETE CASCADE 
           );"""

        # Create Tables
        self.database_manager.db_execute_commit(sql_create_social_alerts_table)
        self.database_manager.db_execute_commit(sql_create_user_in_social_alert_table)


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(SocialAlert(bot))
    logging.info("SocialAlert is ready.")
