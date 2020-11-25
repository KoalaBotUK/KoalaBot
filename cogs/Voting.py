#!/usr/bin/env python

"""
Koala Bot Base Cog code and additional base cog functions
Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import asyncio
import time

from dotenv import load_dotenv

# Libs
import discord
from discord.ext import commands

# Own modules
import KoalaBot
from utils import KoalaDBManager

# Constants
load_dotenv()


class TwoWay(dict):
    def __init__(self, dict_in=None):
        super(TwoWay, self).__init__()
        if dict_in is not None:
            self.update(dict_in)

    def __delitem__(self, key):
        self.pop(self.pop(key))

    def __setitem__(self, key, value):
        # essentially this assert prevents updates to the dict if values are already set
        # which for a 1-1 mapping is reasonable imo, but you could also call __delitem__
        # if you wanted overwriting behaviour to work correctly (but it might be surprising)
        assert key not in self or self[key] == value
        super(TwoWay, self).__setitem__(key, value)
        super(TwoWay, self).__setitem__(value, key)

    def update(self, e, **f):
        # the original update method allows you to pass in keyword args
        # but this version doesn't
        # same amortized cost of O(n) even with the assert
        for key, value in e.items():
            assert key not in self or self[key]==value
            self[key] = value


emote_reference = TwoWay({0: "1️⃣", 1: "2️⃣", 2: "3️⃣",
                          3: "4️⃣", 4: "5️⃣", 5: "6️⃣",
                          6: "7️⃣", 7: "8️⃣", 8: "9️⃣", 9: "🔟"})


# Variables


def is_vote_caller():
    """
    Decorator that returns true if the command invoker has an active vote in the server theyre calling it in
    :return:
    """
    async def predicate(ctx):
        cog = ctx.command.cog
        if KoalaBot.is_dm_channel(ctx):
            return False
        return ctx.author.id in cog.vote_manager.active_votes.keys() and cog.vote_manager.active_votes[ctx.author.id].guild == ctx.guild.id

    return commands.check(predicate)


def vote_is_enabled(ctx):
    """
    A command used to check if the guild has enabled vote
    e.g. @commands.check(KoalaBot.is_admin)
    :param ctx: The context of the message
    :return: True if admin or test, False otherwise
    """
    try:
        result = KoalaBot.check_guild_has_ext(ctx, "Vote")
    except PermissionError:
        result = False
    return result or (
            str(ctx.author) == KoalaBot.TEST_USER and KoalaBot.is_dpytest) or ctx.author.id == 135496683009081345


class VoteManager:
    def __init__(self):
        self.active_votes = {}

    def get_vote(self, ctx):
        return self.active_votes[ctx.author.id]

    def has_active_vote(self, author_id):
        return author_id in self.active_votes.keys()

    def create_vote(self, ctx, title):
        vote = Vote(title, ctx.author.id, ctx.guild.id)
        self.active_votes[ctx.author.id] = vote
        return vote

    def cancel_vote(self, author_id):
        self.active_votes.pop(author_id)

    def run_vote(self, author_id, sent_to):
        vote = self.active_votes[author_id]
        vote.active = True
        vote.sent_to = sent_to

    def was_sent_to(self, msg_id):
        for vote in self.active_votes.values():
            if msg_id in vote.sent_to.values():
                return vote
        return None

    async def close_vote(self, author_id, bot):
        vote = self.active_votes.pop(author_id)
        return await vote.get_results(bot)


class Vote:
    def __init__(self, title, author_id, guild_id):
        self.guild = guild_id
        self.id = author_id
        self.title = title

        self.target_roles = []
        self.chair = author_id
        self.target_voice_channel = None

        self.options = []

        self.active = False
        self.sent_to = {}

    def is_ready(self):
        return len(self.options) > 1

    def add_role(self, role_id):
        self.target_roles.append(role_id)

    def add_roles(self, role_list):
        self.target_roles += role_list

    def remove_role(self, role_id):
        self.target_roles.remove(role_id)

    def remove_roles(self, role_list):
        for role in role_list:
            self.target_roles.remove(role)

    def set_chair(self, chair_id):
        self.chair = chair_id

    def set_vc(self, channel_id=None):
        self.target_voice_channel = channel_id

    def add_option(self, option):
        self.options.append(option)

    def remove_option(self, index):
        del self.options[index-1]

    def start_vote(self):
        self.active = True

    def register_sent(self, user_id, msg_id):
        self.sent_to[user_id] = msg_id

    def create_embed(self):
        embed = discord.Embed(title=self.title)
        for x, option in enumerate(self.options):
            embed.add_field(name=f"{emote_reference[x]} - {option.head}", value=option.body, inline=False)
        return embed

    async def add_reactions(self, msg):
        for x, option in enumerate(self.options):
            await msg.add_reaction(emote_reference[x])

    async def get_results(self, bot):
        results = {}
        for u_id, msg_id in self.sent_to.items():
            user = bot.get_user(u_id)
            msg = await user.fetch_message(msg_id)
            for reaction in msg.reactions:
                if reaction.count > 1:
                    opt = self.options[emote_reference[reaction.emoji]]
                    if opt in results.keys():
                        results[opt] += 1
                    else:
                        results[opt] = 1
                    break
        return results


class Option:
    def __init__(self, head, body):
        self.head = head
        self.body = body


async def add_reactions(vote, msg):
    for x in range(len(vote.options)):
        await msg.add_reaction(emote_reference[x])


async def make_result_embed(vote, results):
    embed = discord.Embed(title=f"{vote.title} Results:")
    for opt, count in results.items():
        embed.add_field(name=opt.head, value=f"{count} votes", inline=False)
    if not results:
        embed.add_field(name="No votes yet!", value="Try giving more time to vote")
    return embed


class Voting(commands.Cog, name="Vote"):
    def __init__(self, bot, db_manager=None):
        self.bot = bot
        self.vote_manager = VoteManager()
        if not db_manager:
            self.DBManager = KoalaDBManager.KoalaDBManager(KoalaBot.DATABASE_PATH, KoalaBot.DB_KEY)
            self.DBManager.insert_extension("Vote", 0, True, True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.update_vote_message(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.update_vote_message(payload)

    @commands.group(name="vote")
    async def vote(self, ctx):
        """
        A group of commands to create a poll to send out to specific members of a discord server.
        :return:
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please use `{KoalaBot.COMMAND_PREFIX}help vote` for more information")

    # @commands.check(KoalaBot.is_admin)
    @vote.command(name="create")
    async def startVote(self, ctx, *, title):
        if self.vote_manager.has_active_vote(ctx.author.id):
            guild_name = self.bot.get_guild(self.vote_manager.get_vote(ctx).guild)
            await ctx.send(f"You already have an active vote in {guild_name}")
            return

        if len(title) > 200:
            await ctx.send("Title too long")
            return

        self.vote_manager.create_vote(ctx, title)
        await ctx.send(f"Vote titled `{title}` created for guild {ctx.guild.name}")

    @is_vote_caller()
    @vote.command(name="addRole")
    async def addRole(self, ctx, *, role: discord.Role):
        vote = self.vote_manager.get_vote(ctx)
        vote.add_role(role.id)
        await ctx.send(f"Vote will be sent to those with the {role.name} role")

    @is_vote_caller()
    @vote.command(name="removeRole")
    async def addRole(self, ctx, *, role: discord.Role):
        vote = self.vote_manager.get_vote(ctx)
        vote.remove_role(role.id)
        await ctx.send(f"Vote will no longer be sent to those with the {role.name} role")

    @is_vote_caller()
    @vote.command(name="addChair")
    async def setChair(self, ctx, *, chair: discord.Member = None):
        vote = self.vote_manager.get_vote(ctx)
        if chair:
            vote.set_chair(chair.id)
            await ctx.send(f"Set chair to {chair.name}")
        else:
            vote.set_chair(ctx.author.id)
            await ctx.send(f"Have made you the chair")

    @is_vote_caller()
    @vote.command(name="setChannel")
    async def setChannel(self, ctx, *, channel: discord.VoiceChannel = None):
        vote = self.vote_manager.get_vote(ctx)
        if channel:
            vote.set_vc(channel.id)
            await ctx.send(f"Set target channel to {channel.name}")
        else:
            vote.set_vc()
            await ctx.send("Removed channel restriction on vote")

    @is_vote_caller()
    @vote.command(name="addOption")
    async def addOption(self, ctx, *, option_string):
        vote = self.vote_manager.get_vote(ctx)
        if len(vote.options) > 9:
            await ctx.send("Vote has maximum number of options already (10)")
        if len(option_string) > 600:
            await ctx.send("Option string is too long")
        header, body = option_string.split("+")
        vote.add_option(Option(header, body))
        await ctx.send(f"Option {header} with description {body} added to vote")

    @is_vote_caller()
    @vote.command(name="removeOption")
    async def removeOption(self, ctx, index: int):
        vote = self.vote_manager.get_vote(ctx)
        vote.remove_option(index)
        await ctx.send(f"Option number {index} removed")

    @is_vote_caller()
    @vote.command(name="preview")
    async def previewVote(self, ctx):
        vote = self.vote_manager.get_vote(ctx)
        await ctx.send(embed=vote.create_embed())

    @is_vote_caller()
    @vote.command(name="cancel")
    async def cancelVote(self, ctx):
        self.vote_manager.cancel_vote(ctx.author.id)
        await ctx.send("Your active vote has been cancelled")

    @is_vote_caller()
    @vote.command(name="send")
    async def sendVote(self, ctx):
        vote = self.vote_manager.get_vote(ctx)
        if len(vote.options) < 2:
            await ctx.send("Please add more than 1 option to vote for")
            return

        users = ctx.guild.members
        if vote.target_voice_channel:
            vc_users = discord.utils.get(ctx.guild.voice_channels, id=vote.target_voice_channel).members
            users = list(set(vc_users) & set(users))
        if vote.target_roles:
            role_users = []
            for role in vote.target_roles:
                role_users += role.members
            role_users = list(dict.fromkeys(role_users))
            users = list(set(role_users) & set(users))
        for user in users:
            if not user.bot:
                msg = await user.send(f"You have been asked to participate in this vote from {ctx.guild.name}.\nPlease react to make your choice (You can change your mind until the vote is closed)", embed=vote.create_embed())
                vote.register_sent(user.id, msg.id)
                await vote.add_reactions(msg)

    @is_vote_caller()
    @vote.command(name="close")
    async def close(self, ctx):
        vote = self.vote_manager.get_vote(ctx)
        results = await self.vote_manager.close_vote(ctx.author.id, self.bot)
        embed = await make_result_embed(vote, results)
        await ctx.send(embed=embed)

    @is_vote_caller()
    @vote.command(name="checkResults")
    async def check(self, ctx):
        vote = self.vote_manager.get_vote(ctx)
        results = await vote.get_results(self.bot)
        embed = await make_result_embed(vote, results)
        await ctx.send(embed=embed)

    # @vote.command(name="testvote")
    # async def testvote(self, ctx):
    #     vote = self.vote_manager.create_vote(ctx, "Test")
    #     vote.add_option(Option("test1", "test1"))
    #     vote.add_option(Option("test2", "test2"))
    #     vote.set_vc(718532674527952920)

    async def update_vote_message(self, payload):
        """
        Updates the vote message with the currently selected option
        :param payload: the reaction event raw payload
        :return:
        """
        vote = self.vote_manager.was_sent_to(payload.message_id)
        user = self.bot.get_user(payload.user_id)
        if vote and not user.bot:
            msg = await user.fetch_message(payload.message_id)
            embed = msg.embeds[0]
            choice = None
            for reaction in msg.reactions:
                if reaction.count > 1:
                    choice = reaction
                    break
            if choice:
                embed.set_footer(text=f"You will be voting for {choice.emoji} - {vote.options[emote_reference[choice.emoji]].head}")
            else:
                embed.set_footer(text="There are no valid choices selected")
            await msg.edit(embed=embed)


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(Voting(bot))
    print("Voting is ready.")
