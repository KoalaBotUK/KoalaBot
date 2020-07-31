#!/usr/bin/env python

"""
Koala Bot Intro Message Cog Code

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports

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

# Variables
base_legal_message = """This server utilizes KoalaBot. In joining this server, you agree to the Terms & Conditions of 
KoalaBot and confirm you have read and understand our Privacy Policy <insert-link-here>"""
DBManager = KoalaDBManager.KoalaDBManager(KoalaBot.DATABASE_PATH)


def get_guild_welcome_message(guild_id: int):
    """
    Retrieves a guild's customised welcome message from the database. Includes the basic legal message constant
    :param guild_id: ID of the guild
    :return: The particular guild's welcome message : str
    """
    welcome_messages = DBManager.db_execute_select(sql_str=
                                                   f"""SELECT * FROM GuildWelcomeMessages WHERE guild_id = '{guild_id}';""")
    if len(welcome_messages) < 1:
        # If there's no current row representing this (for whatever reason), add one to the table
        DBManager.db_execute_commit(sql_str=
                                    f"""INSERT INTO GuildWelcomeMessages (guild_id, welcome_message) VALUES ({guild_id}, 'default message');""")
        welcome_message_row = [0, 'default message']
    else:
        # Return the one that exists
        welcome_message_row = welcome_messages[0]

    guild_welcome_message = welcome_message_row[1]
    return f"{guild_welcome_message} \r\n {base_legal_message}"


async def dm_welcome_message(members, guild_welcome_message):
    """
    DMs members in a guild that guild's welcome message
    :param members: all guild members
    :param guild_welcome_message: The welcome message of the guild
    :return: how many were dm'ed successfully.
    """
    count = 0
    for member in members:
        try:
            await member.send(guild_welcome_message)
            count = count + 1
        except Exception:  # In case of user dms being closed
            pass
    return count


class IntroCog(commands.Cog):
    """
    A discord.py cog with commands pertaining to the welcome messages that a member will receive
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """
        On bot joining guild, add this guild to the database of guild welcome messages.
        :param guild: Guild KoalaBot just joined
        :return: void
        """
        if (len(DBManager.db_execute_select(
                f"""SELECT * FROM GuildWelcomeMessages WHERE guild_id == {guild.id};""")) == 0):
            DBManager.db_execute_commit(
                sql_str=f"""INSERT INTO GuildWelcomeMessages (guild_id,welcome_message) VALUES({guild.id},'default message');""")
        else:
            # There already exists an entry in this table. Reset to default
            DBManager.db_execute_commit(
                f"""UPDATE GuildWelcomeMessages SET welcome_message = '{get_guild_welcome_message(guild.id)}'""")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.member):
        """
        On member joining guild, send DM to member with welcome message.
        :param member: Member which just joined guild
        :return: void
        """
        await dm_welcome_message([member], f"{get_guild_welcome_message(member.guild.id)}")

    @commands.check(KoalaBot.is_owner) # TODO Change to is_admin in production
    @commands.command(name="send_welcome_message")
    async def send_welcome_message(self, ctx):
        """
        Allows admins to send out their welcome message manually to all members of a guild.
        :param ctx: Context of the command
        :param args: Member IDs, Roles or Member mentions to avoid sending the message to
        :return: void
        """
        non_bot_members = [member for member in ctx.guild.members if not member.bot]

        await ctx.send(f"This will DM {len(non_bot_members)} people. Are you sure you wish to do this? Y/N")

        try:
            confirmation_message = await self.bot.wait_for('message', timeout=5.0,
                                                           check=lambda message: message.author == ctx.author)
        except asyncio.TimeoutError:
            await ctx.send('Timed out')
        else:
            conf_msg = confirmation_message.content.rstrip().strip().lower()
            if conf_msg not in ['y', 'n']:
                await ctx.send('Invalid input. Please restart with the command.')
            else:
                if conf_msg == 'n':
                    await ctx.send('Okay, I won\'t send the welcome message out.')
                else:
                    await dm_welcome_message(non_bot_members,
                                             f"{get_guild_welcome_message(ctx.guild.id)}")

    @commands.check(KoalaBot.is_owner) # TODO change to is_admin in production
    @commands.command(name="update_welcome_message")
    async def update_welcome_message(self, ctx, *, new_message: str):
        """
        Allows admins to change their customisable part of the welcome message of a guild.
        :param ctx: Context of the command
        :param new_message: New customised part of the welcome message
        :return: void
        """
        await ctx.send("""Your current welcome message is: \r\n {0} \r\n
        \r\n\r\n Your new welcome message will be: \r\n {1}
        \r\n\r\n Do you accept this change? Y/N""".format(get_guild_welcome_message(ctx.message.guild.id), new_message))

        try:
            confirmation_message = await self.bot.wait_for('message', timeout=5.0,
                                                           check=lambda message: message.author == ctx.author)
        except asyncio.TimeoutError:
            await ctx.send('Timed out')
        else:
            conf_msg = confirmation_message.content.rstrip().strip().lower()
            if conf_msg not in ['y', 'n']:
                await ctx.send('Invalid input. Please restart with the command.')
            else:
                if conf_msg == 'n':
                    await ctx.send('Not changing welcome message then.')
                else:
                    DBManager.db_execute_commit(
                        sql_str=f"""UPDATE GuildWelcomeMessages SET welcome_message = '{new_message}' WHERE guild_id = {ctx.message.guild.id};""")
                    await ctx.send(f"Your new custom part of the welcome message is {new_message}")


def setup(bot: KoalaBot) -> None:
    """
    Loads this cog into the selected bot
    :param bot: The client of the KoalaBot
    """
    bot.add_cog(IntroCog(bot))
