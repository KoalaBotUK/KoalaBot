#!/usr/bin/env python

"""
Koala Bot Text Filter Code

"""

# Libs
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Own modules
import KoalaBot
from utils import KoalaDBManager

# Constants
load_dotenv()
censor = ["fuck","shit"]

# Variables
DBManager = KoalaDBManager.KoalaDBManager(KoalaBot.DATABASE_PATH)

class TextFilterCog(commands.Cog):
    """
    A discord.py cog with commands pertaining to the a Text Filter for admins to monitor their server
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self,message):
        if (any(map(message.content.__contains__,censor))):
            await message.author.send("Watch your language! Your message: '*"+message.content+"*' in #"+message.channel.name+" has been deleted by KoalaBot.")
            await message.delete()

def setup(bot: KoalaBot) -> None:
    """
    Loads this cog into the selected bot
    :param bot: The client of the KoalaBot
    """
    bot.add_cog(TextFilterCog(bot))
