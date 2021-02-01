#!/usr/bin/env python

"""
Koala Bot Vote Cog code and additional base cog functions
Commented using reStructuredText (reST)
"""
# Built-in/Generic Imports
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
    """Class to because a friend was bored and wanted a better way to make a two way dict than the way I had before"""
    def __init__(self, dict_in=None):
        """
        Constructor method
        :param dict_in: an existing dict to make two-way
        """
        super(TwoWay, self).__init__()
        if dict_in is not None:
            self.update(dict_in)

    def __delitem__(self, key):
        """
        Remove an item from the dict
        :param key: the key of the item
        """
        self.pop(self.pop(key))

    def __setitem__(self, key, value):
        """
        Add an item to the dict. Errors if it already exists
        :param key: the key of the item to add
        :param value: the value of the item to add
        """
        assert key not in self or self[key] == value
        super(TwoWay, self).__setitem__(key, value)
        super(TwoWay, self).__setitem__(value, key)

    def update(self, e, **f):
        """
        Update the dict
        :param e: new dict to integrate into the existing one
        :param f: keyword arguments
        """
        for key, value in e.items():
            assert key not in self or self[key]==value
            self[key] = value


class Option:
    def __init__(self, head, body):
        """
        Object holding information about an option
        :param head: the title of the option
        :param body: the description of the option
        """
        self.head = head
        self.body = body


class VoteManager:
    def __init__(self):
        """
        Manages votes for the bot
        """
        self.active_votes = {}

    def get_vote(self, ctx):
        """
        Returns a vote from a given discord context
        :param ctx: discord.Context object from a command
        :return: Relevant vote object
        """
        return self.active_votes[ctx.author.id]

    def has_active_vote(self, author_id):
        """
        Checks if a user already has an active vote somewhere
        :param author_id: the user id of the person trying to create a vote
        :return: True if they have an existing vote, otherwise False
        """
        return author_id in self.active_votes.keys()

    def create_vote(self, ctx, title):
        """
        Creates a vote object and assigns it to a users ID
        :param ctx: discord.Context object from the command
        :param title: title of the vote
        :return: the newly created Vote object
        """
        vote = Vote(title, ctx.author.id, ctx.guild.id)
        self.active_votes[ctx.author.id] = vote
        return vote

    def cancel_vote(self, author_id):
        """
        Removed a vote from the list of active votes
        :param author_id: the user who created the vote
        :return: None
        """
        self.active_votes.pop(author_id)

    def was_sent_to(self, msg_id):
        """
        Checks if a given message was sent by the bot for a vote, so it knows if it should listen for reactions on it.
        :param msg_id: the message that has been reacted on
        :return: the relevant vote for the message, if there is one
        """
        for vote in self.active_votes.values():
            if msg_id in vote.sent_to.values():
                return vote
        return None


class Vote:
    def __init__(self, title, author_id, guild_id):
        """
        An object containing methods and attributes of an active vote
        :param title: title of the vote
        :param author_id: creator of the vote
        :param guild_id: location of the vote
        """
        self.guild = guild_id
        self.id = author_id
        self.title = title

        self.target_roles = []
        self.chair = author_id
        self.target_voice_channel = None

        self.options = []

        self.sent_to = {}

    def is_ready(self):
        """
        Check if the vote is ready to be sent out
        :return: True if ready, False otherwise
        """
        return 1 < len(self.options) < 11

    def add_role(self, role_id):
        """
        Adds a target role to send the vote to
        :param role_id: target role
        :return: None
        """
        self.target_roles.append(role_id)

    def remove_role(self, role_id):
        """
        Removes target role from vote targets
        :param role_id: target role
        :return: None
        """
        self.target_roles.remove(role_id)

    def set_chair(self, chair_id):
        """
        Sets the chair of the vote to the given id
        :param chair_id: target chair
        :return: None
        """
        self.chair = chair_id

    def set_vc(self, channel_id=None):
        """
        Sets the target voice channel to a given channel id
        :param channel_id: target discord voice channel id
        :return: None
        """
        self.target_voice_channel = channel_id

    def add_option(self, option):
        """
        Adds an option to the vote
        :param option: Option object
        :return: None
        """
        self.options.append(option)

    def remove_option(self, index):
        """
        Removes an option from the vote
        :param index: the location in the list of options to remove
        :return: None
        """
        del self.options[index-1]

    def register_sent(self, user_id, msg_id):
        """
        Marks a user as having been sent a message to vote on
        :param user_id: user who was sent the message
        :param msg_id: the id of the message that was sent
        :return:
        """
        self.sent_to[user_id] = msg_id


emote_reference = TwoWay({0: "1️⃣", 1: "2️⃣", 2: "3️⃣",
                               3: "4️⃣", 4: "5️⃣", 5: "6️⃣",
                               6: "7️⃣", 7: "8️⃣", 8: "9️⃣", 9: "🔟"})


def is_vote_caller():
    """
    Decorator that returns true if the command invoker has an active vote in the server they're calling it in
    :return: True if the user has an active vote, false if not
    """
    async def predicate(ctx):
        cog = ctx.command.cog
        if KoalaBot.is_dm_channel(ctx):
            return False
        return ctx.author.id in cog.vote_manager.active_votes.keys() and cog.vote_manager.active_votes[ctx.author.id].guild == ctx.guild.id

    return commands.check(predicate)


def vote_is_enabled(ctx):
    """
    A command used to check if the guild has enabled verify
    e.g. @commands.check(vote_is_enabled)
    :param ctx: The context of the message
    :return: True if enabled or test, False otherwise
    """
    try:
        result = KoalaBot.check_guild_has_ext(ctx, "Vote")
    except PermissionError:
        result = False

    return result or (str(ctx.author) == KoalaBot.TEST_USER and KoalaBot.is_dpytest)


async def add_reactions(vote, msg):
    """
    Adds the relevant reactions from a vote to a given message
    :param vote: the vote the message is for
    :param msg: the discord.Message object to react on
    :return:
    """
    for x in range(len(vote.options)):
        await msg.add_reaction(emote_reference[x])


async def make_result_embed(vote, results):
    """
    Create a discord.Embed object from a set of results for a vote
    :param vote: the vote the results are for
    :param results: the results from the vote
    :return: discord.Embed object to send
    """
    embed = discord.Embed(title=f"{vote.title} Results:")
    for opt, count in results.items():
        embed.add_field(name=opt.head, value=f"{count} votes", inline=False)
    if not results:
        embed.add_field(name="No votes yet!", value="Try giving more time to vote")
    return embed


def create_embed(vote):
    """
    Creates an embed of the current vote configuration
    :return: discord.Embed
    """
    embed = discord.Embed(title=vote.title)
    for x, option in enumerate(vote.options):
        embed.add_field(name=f"{emote_reference[x]} - {option.head}", value=option.body, inline=False)
    return embed


async def get_results(bot, vote):
    """
    Gathers the results from all users who were sent the vote
    :param vote: the vote object
    :param bot: the discord.commands.Bot that sent out the vote messages
    :return: dict of results
    """
    results = {}
    for u_id, msg_id in vote.sent_to.items():
        user = bot.get_user(u_id)
        msg = await user.fetch_message(msg_id)
        for reaction in msg.reactions:
            if reaction.count > 1:
                opt = vote.options[emote_reference[reaction.emoji]]
                if opt in results.keys():
                    results[opt] += 1
                else:
                    results[opt] = 1
                break
    return results


class Voting(commands.Cog, name="Vote"):
    def __init__(self, bot, db_manager=None):
        """
        discord cog to manage the voting interface
        :param bot: the bot that the cog is being run on
        :param db_manager: a database manager (allows testing on a clean database)
        """
        self.bot = bot
        self.vote_manager = VoteManager()
        if not db_manager:
            self.DBManager = KoalaDBManager.KoalaDBManager(KoalaBot.DATABASE_PATH, KoalaBot.DB_KEY)
            self.DBManager.insert_extension("Vote", 0, True, True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        Listens for when a reaction is added to a message
        :param payload: payload of data about the reaction
        """
        await self.update_vote_message(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        Listens for when a reaction is removed from a message
        :param payload: payload of data about the reaction
        """
        await self.update_vote_message(payload)

    @commands.group(name="vote")
    async def vote(self, ctx):
        """
        Use k!vote create <title> to create a vote!
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please use `{KoalaBot.COMMAND_PREFIX}help vote` for more information")

    # @commands.check(KoalaBot.is_admin)
    @commands.check(vote_is_enabled)
    @vote.command(name="create")
    async def startVote(self, ctx, *, title):
        """
        Creates a new vote
        :param title: The title of the vote
        """
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
        """
        Adds a role to the list of roles the vote will be sent to
        If no roles are added, the vote will go to all users in a guild (unless a target voice channel has been set)
        :param role: role id (e.g. 135496683009081345) or a role ping (e.g. @Student)
        """
        vote = self.vote_manager.get_vote(ctx)
        vote.add_role(role.id)
        await ctx.send(f"Vote will be sent to those with the {role.name} role")

    @is_vote_caller()
    @vote.command(name="removeRole")
    async def removeRole(self, ctx, *, role: discord.Role):
        """
           Removes a role to the list of roles the vote will be sent to
           :param role: role id (e.g. 135496683009081345) or a role ping (e.g. @Student)
           """
        vote = self.vote_manager.get_vote(ctx)
        vote.remove_role(role.id)
        await ctx.send(f"Vote will no longer be sent to those with the {role.name} role")

    @is_vote_caller()
    @vote.command(name="setChair")
    async def setChair(self, ctx, *, chair: discord.Member = None):
        """
        Sets the chair of a vote
        If no chair defaults to sending the message to the channel the vote is closed in
        :param chair: user id (e.g. 135496683009081345) or ping (e.g. @ito#8813)
        """
        vote = self.vote_manager.get_vote(ctx)
        if chair:
            vote.set_chair(chair.id)
            await ctx.send(f"Set chair to {chair.name}")
        else:
            vote.set_chair(ctx.author.id)
            await ctx.send(f"Results will just be sent to channel the vote is closed in")

    @is_vote_caller()
    @vote.command(name="setChannel")
    async def setChannel(self, ctx, *, channel: discord.VoiceChannel = None):
        """
        Sets the target voice channel of a vote (Users connected to this channel will receive the vote message)
        If there isn't one set votes will go to all users in a guild (unless target roles have been added)
        :param channel: channel id (e.g. 135496683009081345) or mention (e.g. #cool-channel)
        """
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
        """
        Adds an option to the current vote
        separate the title and description with a "+" e.g. option title+option description
        :param option_string: a title and description for the option separated by a '+'
        """
        vote = self.vote_manager.get_vote(ctx)
        if len(vote.options) > 9:
            await ctx.send("Vote has maximum number of options already (10)")
            return
        if len(option_string) > 600:
            await ctx.send("Option string is too long")
            return
        if "+" not in option_string:
            await ctx.send("Example usage: k!vote addOption option title+option description")
            return
        header, body = option_string.split("+")
        vote.add_option(Option(header, body))
        await ctx.send(f"Option {header} with description {body} added to vote")

    @is_vote_caller()
    @vote.command(name="removeOption")
    async def removeOption(self, ctx, index: int):
        """
        Removes an option from a vote based on it's index
        :param index: the number of the option
        """
        vote = self.vote_manager.get_vote(ctx)
        vote.remove_option(index)
        await ctx.send(f"Option number {index} removed")

    @is_vote_caller()
    @vote.command(name="preview")
    async def previewVote(self, ctx):
        """
        Generates a preview of what users will see with the current configuration of the vote
        """
        vote = self.vote_manager.get_vote(ctx)
        msg = await ctx.send(embed=create_embed(vote))
        await add_reactions(vote, msg)

    @is_vote_caller()
    @vote.command(name="cancel")
    async def cancelVote(self, ctx):
        """
        Cancels a vote you are setting up
        """
        self.vote_manager.cancel_vote(ctx.author.id)
        await ctx.send("Your active vote has been cancelled")

    @is_vote_caller()
    @vote.command(name="send")
    async def sendVote(self, ctx):
        """
        Sends a vote to all users within the restrictions set with the current options added
        """
        vote = self.vote_manager.get_vote(ctx)
        if not vote.is_ready():
            await ctx.send("Please add more than 1 option to vote for")
            return

        users = [x for x in ctx.guild.members if not x.bot]
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
            msg = await user.send(f"You have been asked to participate in this vote from {ctx.guild.name}.\nPlease react to make your choice (You can change your mind until the vote is closed)", embed=create_embed(vote))
            vote.register_sent(user.id, msg.id)
            await add_reactions(vote, msg)
        await ctx.send(f"Sent vote to {len(users)} users")

    @is_vote_caller()
    @vote.command(name="close")
    async def close(self, ctx):
        """
        Ends a vote, and collects the results
        """
        vote = self.vote_manager.get_vote(ctx)
        results = await get_results(self.bot, vote)
        self.vote_manager.cancel_vote(ctx.author.id)
        embed = await make_result_embed(vote, results)
        if vote.chair:
            chair = await self.bot.fetch_user(vote.chair)
            await chair.send(embed=embed)
            await ctx.send(f"Sent results to {chair}")
        else:
            await ctx.send(embed=embed)

    @is_vote_caller()
    @vote.command(name="checkResults")
    async def check(self, ctx):
        """
        Checks the results of a vote without closing it
        """
        vote = self.vote_manager.get_vote(ctx)
        results = await get_results(self.bot, vote)
        embed = await make_result_embed(vote, results)
        await ctx.send(embed=embed)

    @vote.command(name="testVote")
    async def testVote(self, ctx):
        # vote setup for ease of testing
        vote = self.vote_manager.create_vote(ctx, "Test")
        vote.add_option(Option("test1", "test1"))
        vote.add_option(Option("test2", "test2"))
        vote.set_vc(718532674527952920)

    async def update_vote_message(self, payload):
        """
        Updates the vote message with the currently selected option
        :param payload: the reaction event raw payload
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
