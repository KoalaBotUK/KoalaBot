#!/usr/bin/env python

"""
Koala Bot Vote Cog code and additional base cog functions
Commented using reStructuredText (reST)
"""
# Built-in/Generic Imports

# Libs
import discord
from discord.ext import commands, tasks

# Own modules
import koalabot
from koala.db import insert_extension
from . import core
from .db import VoteManager, add_reactions
from .log import logger


# Constants

# Variables


def currently_configuring():
    """
    Decorator that returns true if the command invoker has an active vote in the server they're calling it in
    :return: True if the user has an active vote, false if not
    """
    async def predicate(ctx):
        cog = ctx.command.cog
        if koalabot.is_dm_channel(ctx):
            return False
        return ctx.author.id in cog.vote_manager.configuring_votes.keys() and cog.vote_manager.configuring_votes[ctx.author.id].guild == ctx.guild.id

    return commands.check(predicate)


def has_current_votes():
    async def predicate(ctx):
        cog = ctx.command.cog
        if koalabot.is_dm_channel(ctx):
            return False
        return ctx.author.id in map(lambda x: x[0], cog.vote_manager.vote_lookup.keys())

    return commands.check(predicate)


def vote_is_enabled(ctx):
    """
    A command used to check if the guild has enabled verify
    e.g. @commands.check(vote_is_enabled)
    :param ctx: The context of the message
    :return: True if enabled or test, False otherwise
    """
    try:
        result = koalabot.check_guild_has_ext(ctx, "Vote")
    except PermissionError:
        result = False

    return result or (str(ctx.author) == koalabot.TEST_USER and koalabot.is_dpytest)


class Voting(commands.Cog, name="Vote"):
    def __init__(self, bot):
        """
        discord cog to manage the voting interface
        :param bot: the bot that the cog is being run on
        :param db_manager: a database manager (allows testing on a clean database)
        """
        self.bot = bot
        insert_extension("Vote", 0, True, True)
        self.vote_manager = VoteManager()
        self.vote_manager.load_from_db()
        self.running = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.running:
            self.vote_end_loop.start()
            self.running = True

    async def cog_unload(self):
        self.vote_end_loop.cancel()
        self.running = False

    @tasks.loop(seconds=60.0)
    async def vote_end_loop(self):
        await core.vote_end_loop(self.bot, self.vote_manager)

    @vote_end_loop.before_loop
    async def before_vote_loop(self):
        await self.bot.wait_until_ready()


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        Listens for when a reaction is added to a message
        :param payload: payload of data about the reaction
        """
        await core.update_vote_message(self.bot, payload.message_id, payload.user_id)


    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        Listens for when a reaction is removed from a message
        :param payload: payload of data about the reaction
        """
        await core.update_vote_message(self.bot, payload.message_id, payload.user_id)


    # how do you even procc this
    @commands.check(koalabot.is_admin)
    @commands.check(vote_is_enabled)
    @commands.group(name="vote")
    async def vote(self, ctx):
        """
        Use k!vote create <title> to create a vote!
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please use `{koalabot.COMMAND_PREFIX}help vote` for more information")


    @commands.check(koalabot.is_admin)
    @commands.check(vote_is_enabled)
    @vote.command(name="create")
    async def start_vote(self, ctx, *, title):
        """
        Creates a new vote
        :param title: The title of the vote
        """
        await ctx.send(core.start_vote(self.bot, self.vote_manager, title, ctx.author.id, ctx.guild.id))


    @currently_configuring()
    @commands.check(vote_is_enabled)
    @vote.command(name="addRole")
    async def add_role(self, ctx, *, role: discord.Role):
        """
        Adds a role to the list of roles the vote will be sent to
        If no roles are added, the vote will go to all users in a guild (unless a target voice channel has been set)
        :param role: role id (e.g. 135496683009081345) or a role ping (e.g. @Student)
        """
        await ctx.send(core.set_roles(self.bot, self.vote_manager, ctx.author.id, ctx.guild.id, role.id, "add"))


    @currently_configuring()
    @commands.check(vote_is_enabled)
    @vote.command(name="removeRole")
    async def remove_role(self, ctx, *, role: discord.Role):
        """
       Removes a role to the list of roles the vote will be sent to
       :param role: role id (e.g. 135496683009081345) or a role ping (e.g. @Student)
       """
        await ctx.send(core.set_roles(self.bot, self.vote_manager, ctx.author.id, ctx.guild.id, role.id, "remove"))


    @currently_configuring()
    @commands.check(vote_is_enabled)
    @vote.command(name="setChair")
    async def set_chair(self, ctx, *, chair: discord.Member = None):
        """
        Sets the chair of a vote
        If no chair defaults to sending the message to the channel the vote is closed in
        :param chair: user id (e.g. 135496683009081345) or ping (e.g. @ito#8813)
        """
        await ctx.send(await core.set_chair(self.bot, self.vote_manager, ctx.author.id, getattr(chair, 'id', None)))


    @currently_configuring()
    @commands.check(vote_is_enabled)
    @vote.command(name="setChannel")
    async def set_channel(self, ctx, *, channel: discord.VoiceChannel = None):
        """
        Sets the target voice channel of a vote (Users connected to this channel will receive the vote message)
        If there isn't one set votes will go to all users in a guild (unless target roles have been added)
        :param channel: channel id (e.g. 135496683009081345) or mention (e.g. #cool-channel)
        """
        await ctx.send(core.set_channel(self.bot, self.vote_manager, ctx.author.id, channel.id))


    @currently_configuring()
    @commands.check(vote_is_enabled)
    @vote.command(name="addOption")
    async def add_option(self, ctx, *, option_string):
        """
        Adds an option to the current vote
        separate the title and description with a "+" e.g. option title+option description
        :param option_string: a title and description for the option separated by a '+'
        """
        await ctx.send(core.add_option(self.vote_manager, ctx.author.id, option_string))


    @currently_configuring()
    @commands.check(vote_is_enabled)
    @vote.command(name="removeOption")
    async def remove_option(self, ctx, index: int):
        """
        Removes an option from a vote based on it's index
        :param index: the number of the option
        """
        await ctx.send(core.remove_option(self.vote_manager, ctx.author.id, index))


    @currently_configuring()
    @commands.check(vote_is_enabled)
    @vote.command(name="setEndTime")
    async def set_end_time(self, ctx, *, time_string):
        """
        Sets a specific time for the vote to end. Results will be sent to the chair or owner if you use this, not a channel.
        If the vote has not been sent by the end time it will close automatically once it is sent.
        :param time_string: string representing a time e.g. "2021-03-22 12:56" or "tomorrow at 10am" or "in 5 days and 15 minutes"
        :return:
        """
        await ctx.send(core.set_end_time(self.vote_manager, ctx.author.id, time_string))


    @currently_configuring()
    @commands.check(vote_is_enabled)
    @vote.command(name="preview")
    async def preview_vote(self, ctx):
        """
        Generates a preview of what users will see with the current configuration of the vote
        """
        prev = core.preview(self.vote_manager, ctx.author.id)
        msg = await ctx.send(embed=prev[0])
        await add_reactions(prev[1], msg)


    @commands.check(vote_is_enabled)
    @has_current_votes()
    @vote.command(name="cancel")
    async def cancel_vote(self, ctx, *, title):
        """
        Cancels a vote you are setting up or have sent
        :param title: title of the vote to cancel
        """
        await ctx.send(core.cancel_vote(self.vote_manager, ctx.author.id, title))


    @commands.check(vote_is_enabled)
    @has_current_votes()
    @vote.command("list", aliases=["currentVotes"])
    async def check_current_votes(self, ctx):
        """
        Return a list of all votes you have in this guild.
        :return:
        """
        await ctx.send(embed=core.current_votes(ctx.author.id, ctx.guild.id))


    @currently_configuring()
    @vote.command(name="send")
    async def send_vote(self, ctx):
        """
        Sends a vote to all users within the restrictions set with the current options added
        """
        await ctx.send(await core.send_vote(self.bot, self.vote_manager, ctx.author.id, ctx.guild))


    @commands.check(vote_is_enabled)
    @has_current_votes()
    @vote.command(name="close")
    async def close(self, ctx, *, title):
        """
        Ends a vote, and collects the results
        """
        msg = await core.close(self.bot, self.vote_manager, ctx.author.id, title)
        if type(msg) is list:
            await ctx.send(msg[0], embed=msg[1])
        elif type(msg) is discord.Embed:
            await ctx.send(embed=msg)
        else:
            await ctx.send(msg)


    @commands.check(vote_is_enabled)
    @has_current_votes()
    @vote.command(name="checkResults")
    async def check_results(self, ctx,  *, title):
        """
        Checks the results of a vote without closing it
        """
        msg = await core.results(self.bot, self.vote_manager, ctx.author.id, title)
        if type(msg) is discord.Embed:
            await ctx.send(embed=msg)
        else:
            await ctx.send(msg)


async def setup(bot: koalabot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    await bot.add_cog(Voting(bot))
    logger.info("Voting is ready.")
