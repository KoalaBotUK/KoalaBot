#!/usr/bin/env python

"""
Koala Bot Vote Cog code and additional base cog functions
Commented using reStructuredText (reST)
"""
# Built-in/Generic Imports
from dotenv import load_dotenv
from random import randint
import time
import logging
logging.basicConfig(filename='Vote.log')

# Libs
import discord
from discord.ext import commands, tasks
import parsedatetime.parsedatetime

# Own modules
import KoalaBot

# Constants
load_dotenv()
MIN_ID_VALUE = 100000000000000000
MAX_ID_VALUE = 999999999999999999

# Variables


def currently_configuring():
    """
    Decorator that returns true if the command invoker has an active vote in the server they're calling it in
    :return: True if the user has an active vote, false if not
    """
    async def predicate(ctx):
        cog = ctx.command.cog
        if KoalaBot.is_dm_channel(ctx):
            return False
        return ctx.author.id in cog.vote_manager.configuring_votes.keys() and cog.vote_manager.configuring_votes[ctx.author.id].guild == ctx.guild.id

    return commands.check(predicate)


def has_current_votes():
    async def predicate(ctx):
        cog = ctx.command.cog
        if KoalaBot.is_dm_channel(ctx):
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
        await msg.add_reaction(VoteManager.emote_reference[x])


async def make_result_embed(vote, results):
    """
    Create a discord.Embed object from a set of results for a vote
    :param vote: the vote the results are for
    :param results: the results from the vote
    :return: discord.Embed object to send
    """
    embed = discord.Embed(title=f"{vote.title} Results:")
    for option in vote.options:
        if option not in results.keys():
            results[option] = 0
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
        embed.add_field(name=f"{VoteManager.emote_reference[x]} - {option.head}", value=option.body, inline=False)
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
                opt = vote.options[VoteManager.emote_reference[reaction.emoji]]
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
        if not db_manager:
            self.DBManager = KoalaBot.database_manager
            self.DBManager.insert_extension("Vote", 0, True, True)
        else:
            self.DBManager = db_manager
        self.vote_manager = VoteManager(self.DBManager)
        self.vote_manager.load_from_db()
        self.running = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.running:
            self.vote_end_loop.start()
            self.running = True

    def cog_unload(self):
        self.vote_end_loop.cancel()
        self.running = False

    @tasks.loop(seconds=30.0)
    async def vote_end_loop(self):
        now = time.time()
        votes = self.DBManager.db_execute_select("SELECT * FROM votes WHERE end_time < ?", (now,))
        for v_id, a_id, g_id, title, _, _, end_time in votes:
            if v_id in self.vote_manager.sent_votes.keys():
                vote = self.vote_manager.get_vote_from_id(v_id)
                results = await get_results(self.bot, vote)
                self.vote_manager.cancel_sent_vote(vote.id)
                embed = await make_result_embed(vote, results)
                try:
                    if vote.chair:
                        chair = await self.bot.fetch_user(vote.chair)
                        await chair.send(f"Your vote {title} has closed")
                        await chair.send(embed=embed)
                    else:
                        user = await self.bot.fetch_user(vote.author)
                        await user.send(f"Your vote {title} has closed")
                        await user.send(embed=embed)
                except Exception as e:
                    logging.error(f"error in vote loop: {e}")
        self.DBManager.db_execute_commit("DELETE FROM votes WHERE end_time < ?", (now,))

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


    @commands.check(KoalaBot.is_admin)
    @commands.check(vote_is_enabled)
    @commands.group(name="vote")
    async def vote(self, ctx):
        """
        Use k!vote create <title> to create a vote!
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please use `{KoalaBot.COMMAND_PREFIX}help vote` for more information")

    @commands.check(KoalaBot.is_admin)
    @commands.check(vote_is_enabled)
    @vote.command(name="create")
    async def start_vote(self, ctx, *, title):
        """
        Creates a new vote
        :param title: The title of the vote
        """
        if self.vote_manager.has_active_vote(ctx.author.id):
            guild_name = self.bot.get_guild(self.vote_manager.get_configuring_vote(ctx.author.id).guild)
            await ctx.send(f"You already have an active vote in {guild_name}. Please send that with `{KoalaBot.COMMAND_PREFIX}vote send` before creating a new one.")
            return

        in_db = self.DBManager.db_execute_select("SELECT * FROM Votes WHERE title=? AND author_id=?", (title, ctx.author.id))
        if in_db:
            await ctx.send(f"You already have a vote with title {title} sent!")
            return

        if len(title) > 200:
            await ctx.send("Title too long")
            return

        self.vote_manager.create_vote(ctx.author.id, ctx.guild.id, title)
        await ctx.send(f"Vote titled `{title}` created for guild {ctx.guild.name}. Use `{KoalaBot.COMMAND_PREFIX}help vote` to see how to configure it.")

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
            vote.set_chair(chair.id)
            await ctx.send(f"Set chair to {chair.name}")
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
        if (end_time - now) < 599:
            await ctx.send("Please set the end time to be at least 10 minutes in the future.")
            return
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
        Cancels a vote you are setting up
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
        embed = discord.Embed(title="Your current votes")
        votes = self.DBManager.db_execute_select("SELECT * FROM Votes WHERE author_id=? AND guild_id=?", (ctx.author.id, ctx.guild.id))
        body_string = ""
        for _, _, _, title, _, _, _ in votes:
            body_string += f"{title}\n"
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
            msg = await user.send(f"You have been asked to participate in this vote from {ctx.guild.name}.\nPlease react to make your choice (You can change your mind until the vote is closed)", embed=create_embed(vote))
            vote.register_sent(user.id, msg.id)
            await add_reactions(vote, msg)
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
                await ctx.send(f"That vote has not been sent yet. Please send it to your audience with {KoalaBot.COMMAND_PREFIX}vote send {title}")
            else:
                await ctx.send("You have no votes of that title to close")
            return

        vote = self.vote_manager.get_vote_from_id(vote_id)
        results = await get_results(self.bot, vote)
        self.vote_manager.cancel_sent_vote(vote.id)
        embed = await make_result_embed(vote, results)
        if vote.chair:
            chair = await self.bot.fetch_user(vote.chair)
            await chair.send(embed=embed)
            await ctx.send(f"Sent results to {chair}")
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
                    f"That vote has not been sent yet. Please send it to your audience with {KoalaBot.COMMAND_PREFIX}vote send {title}")
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


class TwoWay(dict):
    """Makes a dict a bijection"""
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
    def __init__(self, head, body, opt_id):
        """
        Object holding information about an option
        :param head: the title of the option
        :param body: the description of the option
        """
        self.id = opt_id
        self.head = head
        self.body = body


class VoteManager:
    def __init__(self, db_manager):
        """
        Manages votes for the bot
        """
        self.configuring_votes = {}
        self.sent_votes = {}
        self.vote_lookup = {}
        self.DBManager = db_manager
        self.set_up_tables()

    emote_reference = TwoWay({0: "1️⃣", 1: "2️⃣", 2: "3️⃣",
                              3: "4️⃣", 4: "5️⃣", 5: "6️⃣",
                              6: "7️⃣", 7: "8️⃣", 8: "9️⃣", 9: "🔟"})

    def generate_unique_opt_id(self):
        used_ids = self.DBManager.db_execute_select("SELECT * FROM VoteOptions")
        used_ids = [x[1] for x in used_ids]
        return self.gen_id(len(used_ids) > (MAX_ID_VALUE - MIN_ID_VALUE))

    def gen_vote_id(self):
        return self.gen_id(len(self.configuring_votes.keys()) == (MAX_ID_VALUE - MIN_ID_VALUE))

    def gen_id(self, cond):
        if cond:
            return None
        while True:
            temp_id = randint(MIN_ID_VALUE, MAX_ID_VALUE)
            if temp_id not in self.configuring_votes.keys():
                return temp_id

    def set_up_tables(self):
        vote_table = """
        CREATE TABLE IF NOT EXISTS Votes (
        vote_id integer NOT NULL,
        author_id integer NOT NULL,
        guild_id integer NOT NULL,
        title text NOT NULL,
        chair_id integer,
        voice_id integer,
        end_time float
        )
        """

        role_table = """
        CREATE TABLE IF NOT EXISTS VoteTargetRoles (
        vote_id integer NOT NULL,
        role_id integer NOT NULL
        )"""

        option_table = """
        CREATE TABLE IF NOT EXISTS VoteOptions (
        vote_id integer NOT NULL,
        opt_id integer NOT NULL,
        option_title text NOT NULL,
        option_desc text NOT NULL
        )"""

        delivered_table = """
        CREATE TABLE IF NOT EXISTS VoteSent (
        vote_id integer NOT NULL,
        vote_receiver_id integer NOT NULL,
        vote_receiver_message integer NOT NULL
        )"""

        self.DBManager.db_execute_commit(vote_table)
        self.DBManager.db_execute_commit(role_table)
        self.DBManager.db_execute_commit(option_table)
        self.DBManager.db_execute_commit(delivered_table)

    def load_from_db(self):
        existing_votes = self.DBManager.db_execute_select("SELECT * FROM Votes")
        for v_id, a_id, g_id, title, chair_id, voice_id, end_time in existing_votes:
            vote = Vote(v_id, title, a_id, g_id, self.DBManager)
            vote.set_chair(chair_id)
            vote.set_vc(voice_id)
            self.vote_lookup[(a_id, title)] = v_id

            target_roles = self.DBManager.db_execute_select("SELECT * FROM VoteTargetRoles WHERE vote_id=?", (v_id,))
            if target_roles:
                for _, r_id in target_roles:
                    vote.add_role(r_id)

            options = self.DBManager.db_execute_select("SELECT * FROM VoteOptions WHERE vote_id=?", (v_id,))
            if options:
                for _, o_id, o_title, o_desc in options:
                    vote.add_option(Option(o_title, o_desc, opt_id=o_id))

            delivered = self.DBManager.db_execute_select("SELECT * FROM VoteSent WHERE vote_id=?", (v_id,))
            if delivered:
                self.sent_votes[v_id] = vote
                for _, rec_id, msg_id in delivered:
                    vote.register_sent(rec_id, msg_id)
            else:
                self.configuring_votes[a_id] = vote

    def get_vote_from_id(self, v_id):
        """
        Returns a vote from a given discord context
        :param v_id: id of the vote
        :return: Relevant vote object
        """
        return self.sent_votes[v_id]

    def get_configuring_vote(self, author_id):
        return self.configuring_votes[author_id]

    def has_active_vote(self, author_id):
        """
        Checks if a user already has an active vote somewhere
        :param author_id: id of the author
        :return: True if they have an existing vote, otherwise False
        """
        return author_id in self.configuring_votes.keys()

    def create_vote(self, author_id, guild_id, title):
        """
        Creates a vote object and assigns it to a users ID
        :param author_id: id of the author of the vote
        :param guild_id: id of the guild of the vote
        :param title: title of the vote
        :return: the newly created Vote object
        """
        v_id = self.gen_vote_id()
        vote = Vote(v_id, title, author_id, guild_id, self.DBManager)
        self.vote_lookup[(author_id, title)] = v_id
        self.configuring_votes[author_id] = vote
        self.DBManager.db_execute_commit("INSERT INTO Votes VALUES (?, ?, ?, ?, ?, ?, ?)",
                                         (vote.id, author_id, vote.guild, vote.title, vote.chair, vote.target_voice_channel, vote.end_time))
        return vote

    def cancel_sent_vote(self, v_id):
        """
        Removed a vote from the list of active votes
        :param v_id: the vote id
        :return: None
        """
        vote = self.sent_votes.pop(v_id)
        self.cancel_vote(vote)

    def cancel_configuring_vote(self, author_id):
        vote = self.configuring_votes.pop(author_id)
        self.cancel_vote(vote)

    def cancel_vote(self, vote):
        self.vote_lookup.pop((vote.author, vote.title))
        self.DBManager.db_execute_commit("DELETE FROM Votes WHERE vote_id=?", (vote.id,))
        self.DBManager.db_execute_commit("DELETE FROM VoteTargetRoles WHERE vote_id=?", (vote.id,))
        self.DBManager.db_execute_commit("DELETE FROM VoteOptions WHERE vote_id=?", (vote.id,))
        self.DBManager.db_execute_commit("DELETE FROM VoteSent WHERE vote_id=?", (vote.id,))

    def was_sent_to(self, msg_id):
        """
        Checks if a given message was sent by the bot for a vote, so it knows if it should listen for reactions on it.
        :param msg_id: the message that has been reacted on
        :return: the relevant vote for the message, if there is one
        """
        for vote in self.sent_votes.values():
            if msg_id in vote.sent_to.values():
                return vote
        return None


class Vote:
    def __init__(self, v_id, title, author_id, guild_id, db_manager):
        """
        An object containing methods and attributes of an active vote
        :param title: title of the vote
        :param author_id: creator of the vote
        :param guild_id: location of the vote
        """
        self.guild = guild_id
        self.id = v_id
        self.author = author_id
        self.title = title
        self.DBManager = db_manager

        self.target_roles = []
        self.chair = None
        self.target_voice_channel = None
        self.end_time = None

        self.options = []

        self.sent_to = {}

    def is_ready(self):
        """
        Check if the vote is ready to be sent out
        :return: True if ready, False otherwise
        """
        return 1 < len(self.options) < 11 and not self.sent_to

    def add_role(self, role_id):
        """
        Adds a target role to send the vote to
        :param role_id: target role
        :return: None
        """
        if self.sent_to:
            return
        self.target_roles.append(role_id)
        in_db = self.DBManager.db_execute_select("SELECT * FROM VoteTargetRoles WHERE vote_id=? AND role_id=?", (self.id, role_id))
        if not in_db:
            self.DBManager.db_execute_commit("INSERT INTO VoteTargetRoles VALUES (?, ?)", (self.id, role_id))

    def remove_role(self, role_id):
        """
        Removes target role from vote targets
        :param role_id: target role
        :return: None
        """
        if self.sent_to:
            return
        self.target_roles.remove(role_id)
        self.DBManager.db_execute_commit("DELETE FROM VoteTargetRoles WHERE vote_id=? AND role_id=?", (self.id, role_id))

    def set_end_time(self, time=None):
        """
        Sets the end time of the vote.
        :param time: time in unix time
        :return:
        """
        self.end_time = time
        self.DBManager.db_execute_commit("UPDATE votes SET end_time=? WHERE vote_id=?", (time, self.id))

    def set_chair(self, chair_id=None):
        """
        Sets the chair of the vote to the given id
        :param chair_id: target chair
        :return: None
        """
        if self.sent_to:
            return
        self.chair = chair_id
        self.DBManager.db_execute_commit("UPDATE Votes SET chair_id=? WHERE vote_id=?", (chair_id, self.id))

    def set_vc(self, channel_id=None):
        """
        Sets the target voice channel to a given channel id
        :param channel_id: target discord voice channel id
        :return: None
        """
        if self.sent_to:
            return
        self.target_voice_channel = channel_id
        self.DBManager.db_execute_commit("UPDATE Votes SET voice_id=? WHERE vote_id=?", (channel_id, self.id))

    def add_option(self, option):
        """
        Adds an option to the vote
        :param option: Option object
        :return: None
        """
        if self.sent_to:
            return
        self.options.append(option)
        in_db = self.DBManager.db_execute_select("SELECT * FROM VoteOptions WHERE opt_id=?", (option.id,))
        if not in_db:
            self.DBManager.db_execute_commit("INSERT INTO VoteOptions VALUES (?, ?, ?, ?)", (self.id, option.id, option.head, option.body))

    def remove_option(self, index):
        """
        Removes an option from the vote
        :param index: the location in the list of options to remove
        :return: None
        """
        if self.sent_to:
            return
        opt = self.options.pop(index-1)
        self.DBManager.db_execute_commit("DELETE FROM VoteOptions WHERE vote_id=? AND opt_id=?", (self.id, opt.id))

    def register_sent(self, user_id, msg_id):
        """
        Marks a user as having been sent a message to vote on
        :param user_id: user who was sent the message
        :param msg_id: the id of the message that was sent
        :return:
        """
        self.sent_to[user_id] = msg_id
        in_db = self.DBManager.db_execute_select("SELECT * FROM VoteSent WHERE vote_receiver_message=?", (msg_id,))
        if not in_db:
            self.DBManager.db_execute_commit("INSERT INTO VoteSent VALUES (?, ?, ?)", (self.id, user_id, msg_id))


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(Voting(bot))
    print("Voting is ready.")
