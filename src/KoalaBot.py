#!/usr/bin/env python

"""
Koala Bot

Commented using reStructuredText (reST)

ToDo
    create and use a database for multiple servers
    server and clients where server responds saying the server is down if lost connection
"""
# Futures

# Built-in/Generic Imports
import os
import sys
import configparser
import shutil
import time
import codecs

# Libs
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

# Own modules

__author__ = "Jack Draper, Kieran Allinson, Viraj Shah"
__copyright__ = "Copyright (c) 2020 KoalaBot"
__credits__ = ["Jack Draper", "Kieran Allinson", "Viraj Shah"]
__license__ = "MIT License"
__version__ = "0.0.1"
__maintainer__ = "Jack Draper, Kieran Allinson, Viraj Shah"
__email__ = "koalabotuk@gmail.com"
__status__ = "Development"
# "Prototype", "Development", or "Production"

# Constants
COGS_DIR = ".\cogs"

started = False

BOT_TOKEN = os.environ['DISCORD_TOKEN']

os.system("title "+"KoalaBot")
client = commands.Bot(command_prefix="k!")


@client.event
async def on_ready():
    """
    Ran after all cogs have been started and bot is ready
    :return:
    """
    global started
    if not started:
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="you sleep"))
        started = True
    print("Bot is ready.")


# ---------------------------------------------------------------------------------------------- To be set as owner only
@client.command()
@commands.has_permissions(administrator=True)
async def change_activity(ctx, activity, name):
    """
    Allows admins to change the activity of the bot
    :param ctx: Context of the command
    :param activity: The new activity of the bot
    :param name: The name of the activity
    :return:
    """
    if str.lower(activity) == "watching":
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=name))
        await ctx.send(f"I am now watching {name}")
    elif str.lower(activity) == "playing":
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=name))
        await ctx.send(f"I am now playing {name}")
    else:
        await ctx.send("That is not a valid activity, sorry!\nTry 'playing' or 'watching'")


@client.event
async def on_member_join(member):
    """
    When a member joins console will receive a notification
    :param member: Member that has joined
    :return:
    """
    print(f"{member} has joined the server")


@client.event
async def on_member_remove(member):
    """
    When a member is removed (kicked or left) console receives a notification
    :param member: Member that has left
    :return:
    """
    print(f"{member} has left the server")


@client.command()
async def ping(ctx):
    """
    Returns the ping of the bot
    :param ctx: Context of the command
    :return:
    """
    await ctx.send(f"Pong! {round(client.latency*1000)}ms")


#@client.command(aliases=['8ball','test'])
#async def _8ball(ctx, *, question):
#    ctx.send(f'Question = {question}')


@client.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, amount=2):
    """
    Clears a given number of messages from the given channel
    :param ctx: Context of the command
    :param amount: Amount of lines to delete
    :return:
    """
    await ctx.channel.purge(limit=amount)


@client.command()
@commands.is_owner()
async def load_cog(ctx, extension):
    """
    Loads a cog from the cogs folder
    :param ctx: Context of the command
    :param extension: The name of the cog
    :return:
    """
    client.load_extension(f'cogs.{extension}')


@client.command()
@commands.is_owner()
async def unload_cog(ctx, extension):
    """
    Unloads a running cog
    :param ctx: Context of the command
    :param extension: The name of the cog
    :return:
    """
    client.unload_extension(f'cogs.{extension}')




# Loads all cogs in COGS_DIR
for filename in os.listdir(COGS_DIR):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')




# Starts bot using the given BOT_ID
client.run(BOT_TOKEN)
