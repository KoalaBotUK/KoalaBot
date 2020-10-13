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
from utils.KoalaColours import *
from utils.KoalaUtils import extract_id, error_embed, is_channel_in_guild

# Constants
load_dotenv()
TWITTER_CLIENT_ID = os.environ['TWITTER_CLIENT_ID']
TWITTER_CLIENT_SECRET = os.environ['TWITTER_CLIENT_SECRET']
TWITTER_ACCESS_TOKEN = os.environ['TWITTER_ACCESS_TOKEN']
TWITTER_TOKEN_SECRET = os.environ['TWITTER_TOKEN_SECRET']


# Variables

class SocialAlert(commands.Cog):
    """
        A discord.py cog for providing social feed updates from Facebook, Instagram and Twitter
    """

    def __init__(self, bot):
        self.bot = bot
        self.twitter_handler = TwitterAPIHandler(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET,
                                                 TWITTER_ACCESS_TOKEN, TWITTER_TOKEN_SECRET)

    # TODO: Extracting twitter display name from id and vice versa
    @commands.command(name="twitterAdd", aliases=['add_user_to_twitter_alert'])
    @commands.check(KoalaBot.is_admin)
    async def add_user_to_twitter_alert(self, ctx, raw_channel_id, twitter_id=None):
        """

        :param twitter_id:
        :param ctx:
        :param raw_channel_id:
        :param twitter_id:
        :return:
        """
        KoalaBot.check_guild_has_ext(ctx, "SocialAlert")

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
    async def remove_user_from_twitter_alert(self, ctx, raw_channel_id, twitter_id=None):
        """

        :param ctx:
        :param raw_channel_id:
        :param twitter_id:
        :return:
        """

        KoalaBot.check_guild_has_ext(ctx, "SocialAlert")

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
            return discord.Embed(title=str(type("yeet").__name__), description=str("yeet"), colour=ERROR_RED)
        except:
            print("Error during authentication")

        #tweet_stream = tweepy.Stream(auth=self.twitter_handler.api, listener=self.twitter_handler.stream_listener)
        #current_text = tweet_stream.filter(follow=self.twitter_handler.followed_accounts, is_async=True)
        #tweet_embed = create_social_embed("twitter", "template_user", current_text)
        #channel = self.bot.get_channel("channel_id")
        #channel.send(embed=tweet_embed)


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


class FacebookGraphAPIHandler:
    """
    A wrapper to interact with the Facebook GraphAPI
    """

    def __init__(self, client_id: str, client_secret: str, short_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.short_token = short_token
        self.oauth_token = self.get_new_facebook_oauth()
        self.graph = facebook.GraphAPI(self.oauth_token)

    def get_new_facebook_oauth(self):
        """
        Get a new long-lived access token from Facebook
        :return: New long-lived access token
        """
        access_token_url = "https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id={}&client_secret={}&fb_exchange_token={}".format(
            self.client_id, self.client_secret, self.short_token)
        return requests.get(access_token_url).json()['access_token']

    def get_post_info(self, page_id):
        """
        Gets default fields for the most recent post on a page feed
        :param page_id: ID of the page
        :return: Dictionary with the post's data
        """
        return self.graph.get_connections(page_id, connection_name="feed", limit=1)

    def get_page_info(self, page_id):
        """
        Gets default fields (name and id) for a specified page
        :param page_id: ID of the page
        :return: Dictionary with the page's data
        """
        return self.graph.get_object(page_id)


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(SocialAlert(bot))
