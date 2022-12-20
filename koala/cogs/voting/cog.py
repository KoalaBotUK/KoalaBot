#!/usr/bin/env python

"""
Koala Bot Vote Cog code and additional base cog functions
Commented using reStructuredText (reST)
"""
# Built-in/Generic Imports
import time

# Libs
import discord
import parsedatetime.parsedatetime
from discord.ext import commands, tasks
from sqlalchemy import select, delete, update

# Own modules
import koalabot
from koala.db import session_manager, insert_extension
from .db import VoteManager, get_results, create_embed, add_reactions
from .log import logger
from .models import Votes
from .option import Option
from .utils import make_result_embed


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
        try:
            with session_manager() as session:
                now = time.time()
                votes = session.execute(select(Votes.vote_id, Votes.author_id, Votes.guild_id, Votes.title, Votes.end_time)
                                        .where(Votes.end_time < now)).all()
                for v_id, a_id, g_id, title, end_time in votes:
                    if v_id in self.vote_manager.sent_votes.keys():
                        vote = self.vote_manager.get_vote_from_id(v_id)
                        results = await get_results(self.bot, vote)
                        embed = await make_result_embed(vote, results)
                        try:
                            if vote.chair:
                                try:
                                    chair = await self.bot.fetch_user(vote.chair)
                                    await chair.send(f"Your vote {title} has closed")
                                    await chair.send(embed=embed)
                                except discord.Forbidden:
                                    user = await self.bot.fetch_user(vote.author)
                                    await user.send(f"Your vote {title} has closed")
                                    await user.send(embed=embed)
                            else:
                                try:
                                    user = await self.bot.fetch_user(vote.author)
                                    await user.send(f"Your vote {title} has closed")
                                    await user.send(embed=embed)
                                except discord.Forbidden:
                                    guild = await self.bot.fetch_guild(vote.guild)
                                    user = await self.bot.fetch_user(guild.owner_id)
                                    await user.send(f"A vote in your guild titled {title} has closed and the chair is unavailable.")
                                    await user.send(embed=embed)
                            session.execute(delete(Votes).filter_by(vote_id=vote.id))
                            session.commit()
                            self.vote_manager.cancel_sent_vote(vote.id)
                        except Exception as e:
                            session.execute(update(Votes).filter_by(vote_id=vote.id).values(end_time=time.time() + 86400))
                            session.commit()
                            logger.error(f"error in vote loop: {e}")
        except Exception as e:
            logger.error("Exception in outer vote loop: %s" % e, exc_info=e)

    @vote_end_loop.before_loop
    async def before_vote_loop(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        Listens for when a reaction is added to a message
        :param payload: payload of data about the reaction
        """
        await self.update_vote_message(payload.message_id, payload.user_id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        Listens for when a reaction is removed from a message
        :param payload: payload of data about the reaction
        """
        await self.update_vote_message(payload.message_id, payload.user_id)

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
        with session_manager() as session:
            if self.vote_manager.has_active_vote(ctx.author.id):
                guild_name = self.bot.get_guild(self.vote_manager.get_configuring_vote(ctx.author.id).guild)
                await ctx.send(f"You already have an active vote in {guild_name}. Please send that with `{koalabot.COMMAND_PREFIX}vote send` before creating a new one.")
                return

            in_db = session.execute(select(Votes).filter_by(title=title, author_id=ctx.author.id)).all()
            if in_db:
                await ctx.send(f"You already have a vote with title {title} sent!")
                return

            if len(title) > 200:
                await ctx.send("Title too long")
                return

            self.vote_manager.create_vote(ctx.author.id, ctx.guild.id, title)
            await ctx.send(f"Vote titled `{title}` created for guild {ctx.guild.name}. Use `{koalabot.COMMAND_PREFIX}help vote` to see how to configure it.")

    @currently_configuring()
    @commands.check(vote_is_enabled)
    @vote.command(name="addRole")
    async def add_role(self, ctx, *, role: discord.Role):
        """
        Adds a role to the list of roles the vote will be sent to
        If no roles are added, the vote will go to all users in a guild (unless a target voice channel has been set)
        :param role: role id (e.g. 135496683009081345) or a role ping (e.g. @Student)
        """
        vote = self.vote_manager.get_configuring_vote(ctx.author.id)
        vote.add_role(role.id)
        await ctx.send(f"Vote will be sent to those with the {role.name} role")

    @currently_configuring()
    @commands.check(vote_is_enabled)
    @vote.command(name="removeRole")
    async def remove_role(self, ctx, *, role: discord.Role):
        """
       Removes a role to the list of roles the vote will be sent to
       :param role: role id (e.g. 135496683009081345) or a role ping (e.g. @Student)
       """
        vote = self.vote_manager.get_configuring_vote(ctx.author.id)
        vote.remove_role(role.id)
        await ctx.send(f"Vote will no longer be sent to those with the {role.name} role")

    @currently_configuring()
    @commands.check(vote_is_enabled)
    @vote.command(name="setChair")
    async def set_chair(self, ctx, *, chair: discord.Member = None):
        """
        Sets the chair of a vote
        If no chair defaults to sending the message to the channel the vote is closed in
        :param chair: user id (e.g. 135496683009081345) or ping (e.g. @ito#8813)
        """
        vote = self.vote_manager.get_configuring_vote(ctx.author.id)
        if chair:
            try:
                await chair.send(f"You have been selected as the chair for vote titled {vote.title}")
                vote.set_chair(chair.id)
                await ctx.send(f"Set chair to {chair.name}")
            except discord.Forbidden:
                await ctx.send("Chair not set as requested user is not accepting direct messages.")
        else:
            vote.set_chair(None)
            await ctx.send(f"Results will be sent to the channel vote is closed in")

    @currently_configuring()
    @commands.check(vote_is_enabled)
    @vote.command(name="setChannel")
    async def set_channel(self, ctx, *, channel: discord.VoiceChannel = None):
        """
        Sets the target voice channel of a vote (Users connected to this channel will receive the vote message)
        If there isn't one set votes will go to all users in a guild (unless target roles have been added)
        :param channel: channel id (e.g. 135496683009081345) or mention (e.g. #cool-channel)
        """
        vote = self.vote_manager.get_configuring_vote(ctx.author.id)
        if channel:
            vote.set_vc(channel.id)
            await ctx.send(f"Set target channel to {channel.name}")
        else:
            vote.set_vc()
            await ctx.send("Removed channel restriction on vote")

    @currently_configuring()
    @commands.check(vote_is_enabled)
    @vote.command(name="addOption")
    async def add_option(self, ctx, *, option_string):
        """
        Adds an option to the current vote
        separate the title and description with a "+" e.g. option title+option description
        :param option_string: a title and description for the option separated by a '+'
        """
        vote = self.vote_manager.get_configuring_vote(ctx.author.id)
        if len(vote.options) > 9:
            await ctx.send("Vote has maximum number of options already (10)")
            return
        current_option_length = sum([len(x.head) + len(x.body) for x in vote.options])
        if current_option_length + len(option_string) > 1500:
            await ctx.send(f"Option string is too long. The total length of all the vote options cannot be over 1500 characters.")
            return
        if "+" not in option_string:
            await ctx.send("Example usage: k!vote addOption option title+option description")
            return
        header, body = option_string.split("+")
        vote.add_option(Option(header, body, self.vote_manager.generate_unique_opt_id()))
        await ctx.send(f"Option {header} with description {body} added to vote")

    @currently_configuring()
    @commands.check(vote_is_enabled)
    @vote.command(name="removeOption")
    async def remove_option(self, ctx, index: int):
        """
        Removes an option from a vote based on it's index
        :param index: the number of the option
        """
        vote = self.vote_manager.get_configuring_vote(ctx.author.id)
        vote.remove_option(index)
        await ctx.send(f"Option number {index} removed")

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
        now = time.time()
        vote = self.vote_manager.get_configuring_vote(ctx.author.id)
        cal = parsedatetime.Calendar()
        end_time_readable = cal.parse(time_string)[0]
        end_time = time.mktime(end_time_readable)
        if (end_time - now) < 0:
            await ctx.send("You can't set a vote to end in the past")
            return
        # if (end_time - now) < 599:
        #     await ctx.send("Please set the end time to be at least 10 minutes in the future.")
        #     return
        vote.set_end_time(end_time)
        await ctx.send(f"Vote set to end at {time.strftime('%Y-%m-%d %H:%M:%S', end_time_readable)} UTC")

    @currently_configuring()
    @commands.check(vote_is_enabled)
    @vote.command(name="preview")
    async def preview_vote(self, ctx):
        """
        Generates a preview of what users will see with the current configuration of the vote
        """
        vote = self.vote_manager.get_configuring_vote(ctx.author.id)
        msg = await ctx.send(embed=create_embed(vote))
        await add_reactions(vote, msg)

    @commands.check(vote_is_enabled)
    @has_current_votes()
    @vote.command(name="cancel")
    async def cancel_vote(self, ctx, *, title):
        """
        Cancels a vote you are setting up or have sent
        :param title: title of the vote to cancel
        """
        v_id = self.vote_manager.vote_lookup[(ctx.author.id, title)]
        if v_id in self.vote_manager.sent_votes.keys():
            self.vote_manager.cancel_sent_vote(v_id)
        else:
            self.vote_manager.cancel_configuring_vote(ctx.author.id)
        await ctx.send(f"Vote {title} has been cancelled.")

    @commands.check(vote_is_enabled)
    @has_current_votes()
    @vote.command("list", aliases=["currentVotes"])
    async def check_current_votes(self, ctx):
        """
        Return a list of all votes you have in this guild.
        :return:
        """
        with session_manager() as session:
            embed = discord.Embed(title="Your current votes")
            votes = session.execute(select(Votes.title).filter_by(author_id=ctx.author.id, guild_id=ctx.guild.id)).all()
            body_string = ""
            for title in votes:
                body_string += f"{title[0]}\n"
            embed.add_field(name="Vote Title", value=body_string, inline=False)
            await ctx.send(embed=embed)

    @currently_configuring()
    @vote.command(name="send")
    async def send_vote(self, ctx):
        """
        Sends a vote to all users within the restrictions set with the current options added
        """
        vote = self.vote_manager.get_configuring_vote(ctx.author.id)

        if not vote.is_ready():
            await ctx.send("Please add more than 1 option to vote for")
            return

        self.vote_manager.configuring_votes.pop(ctx.author.id)
        self.vote_manager.sent_votes[vote.id] = vote

        users = [x for x in ctx.guild.members if not x.bot]
        if vote.target_voice_channel:
            vc_users = discord.utils.get(ctx.guild.voice_channels, id=vote.target_voice_channel).members
            users = list(set(vc_users) & set(users))
        if vote.target_roles:
            role_users = []
            for role_id in vote.target_roles:
                role = discord.utils.get(ctx.guild.roles, id=role_id)
                role_users += role.members
            role_users = list(dict.fromkeys(role_users))
            users = list(set(role_users) & set(users))
        for user in users:
            try:
                msg = await user.send(f"You have been asked to participate in this vote from {ctx.guild.name}.\nPlease react to make your choice (You can change your mind until the vote is closed)", embed=create_embed(vote))
                vote.register_sent(user.id, msg.id)
                await add_reactions(vote, msg)
            except discord.Forbidden:
                logger.error(f"tried to send vote to user {user.id} but direct messages are turned off.")
        await ctx.send(f"Sent vote to {len(users)} users")

    @commands.check(vote_is_enabled)
    @has_current_votes()
    @vote.command(name="close")
    async def close(self, ctx, *, title):
        """
        Ends a vote, and collects the results
        """
        vote_id = self.vote_manager.vote_lookup[(ctx.author.id, title)]
        if vote_id not in self.vote_manager.sent_votes.keys():
            if ctx.author.id in self.vote_manager.configuring_votes.keys():
                await ctx.send(f"That vote has not been sent yet. Please send it to your audience with {koalabot.COMMAND_PREFIX}vote send {title}")
            else:
                await ctx.send("You have no votes of that title to close")
            return

        vote = self.vote_manager.get_vote_from_id(vote_id)
        results = await get_results(self.bot, vote)
        self.vote_manager.cancel_sent_vote(vote.id)
        embed = await make_result_embed(vote, results)
        if vote.chair:
            try:
                chair = await self.bot.fetch_user(vote.chair)
                await chair.send(embed=embed)
                await ctx.send(f"Sent results to {chair}")
            except discord.Forbidden:
                await ctx.send("Chair does not accept direct messages, sending results here.")
                await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed)

    @commands.check(vote_is_enabled)
    @has_current_votes()
    @vote.command(name="checkResults")
    async def check_results(self, ctx,  *, title):
        """
        Checks the results of a vote without closing it
        """
        vote_id = self.vote_manager.vote_lookup[(ctx.author.id, title)]
        if vote_id not in self.vote_manager.sent_votes.keys():
            if ctx.author.id in self.vote_manager.configuring_votes.keys():
                await ctx.send(
                    f"That vote has not been sent yet. Please send it to your audience with {koalabot.COMMAND_PREFIX}vote send {title}")
            else:
                await ctx.send("You have no votes of that title to check")
            return

        vote = self.vote_manager.get_vote_from_id(vote_id)
        results = await get_results(self.bot, vote)
        embed = await make_result_embed(vote, results)
        await ctx.send(embed=embed)

    async def update_vote_message(self, message_id, user_id):
        """
        Updates the vote message with the currently selected option
        :param message_id: id of the message that was reacted on
        :param user_id: id of the user who reacted
        """
        vote = self.vote_manager.was_sent_to(message_id)
        user = self.bot.get_user(user_id)
        if vote and not user.bot:
            msg = await user.fetch_message(message_id)
            embed = msg.embeds[0]
            choice = None
            for reaction in msg.reactions:
                if reaction.count > 1:
                    choice = reaction
                    break
            if choice:
                embed.set_footer(text=f"You will be voting for {choice.emoji} - {vote.options[VoteManager.emote_reference[choice.emoji]].head}")
            else:
                embed.set_footer(text="There are no valid choices selected")
            await msg.edit(embed=embed)


async def setup(bot: koalabot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    await bot.add_cog(Voting(bot))
    logger.info("Voting is ready.")
