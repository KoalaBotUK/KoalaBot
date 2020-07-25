#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions
Commented using reStructuredText (reST)
TODO: - FB GraphAPI Wrapper
      - Page Access Tokens
      - Display top item in feed
      - similar structure for Instagram + Twitter

"""
# Futures

# Built-in/Generic Imports
import os
import time
import asyncio
import concurrent.futures

# Libs
import discord
from discord.ext import commands
from dotenv import load_dotenv
import requests

# Own modules
import KoalaBot

# Constants
load_dotenv()


# Variables

class SocialAlert(commands.Cog):
    '''
        A discord.py cog for providing social feed updates from Facebook, Instagram and Twitter
    '''
    pass


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(SocialAlert(bot))
