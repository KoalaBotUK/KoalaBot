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
emote_reference = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣",
                   4: "4️⃣", 5: "5️⃣", 6: "6️⃣",
                   7: "7️⃣", 8: "8️⃣", 9: "9️⃣", 10: "🔟"}
reverse_reference = {v: k for k, v in emote_reference.items()}


# Variables


def is_vote_caller():
    async def predicate(ctx):
        cog = ctx.command.cog
        if KoalaBot.is_dm_channel(ctx):
            return False
        return ctx.author.id in cog.vote_manager.active_votes.keys() and cog.vote_manager.active_votes[
            ctx.author.id].target_server == ctx.guild.id

    return commands.check(predicate)


def test_is_admin(ctx):
    return KoalaBot.is_admin(ctx) or ctx.author.id == 135496683009081345


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

    @staticmethod
    async def wait_for_message(bot: discord.Client, ctx: commands.Context, timeout: float = 60.0, check=lambda message: message.author == ctx.author):
        try:
            msg = await bot.wait_for('message', timeout=timeout, check=check)
            return msg
        except Exception:
            msg = None
        return msg

    @commands.group(name="vote")
    async def vote(self, ctx):
        """
        A group of commands to create a poll to send out to specific members of a discord server.
        :return:
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please use `{KoalaBot.COMMAND_PREFIX}help vote` for more information")

    # @commands.check(KoalaBot.is_admin)
    @vote.command(name="create", brief="Start the creation of a vote.")
    async def startVote(self, ctx, *, title):
        """
        Start the creation of a vote.
        Admin only due to the potential to send messages to the whole server.
        :param title: the title of the vote
        :return:
        """
        if self.vote_manager.vote_exists(ctx.author.id):
            await ctx.send(
                "You already have an active vote somewhere, please close it before trying to create a new one.")
            return

        if len(title) > 200:
            raise self.OptionsError("Title too long")

        msg_content = [
            f"You have started making a vote titled '{title}'.\nEach upcoming prompt has a 60 second timeout.",
            "Do you want this vote to be sent to users with specific roles? If so ping each role you want (e.g. @student @staff). If not, reply 'no'.",
            "Vote will be sent to users with any of the following roles: ",
            "Do you want this vote to be sent to users in a specific voice channel? If so please respond with the corresponding number from this list:",
            "If not, replay 'no'.",
            "Vote will be sent to users in this voice channel: ",
            "Who is chairing the vote? (Vote results will be sent to them as well as the channel the vote is closed from).",
            "Ping the user or reply 'no' to default to you.",
            "Results will be sent to: ",
            f"Vote creation is complete, for further commands view {KoalaBot.COMMAND_PREFIX}help vote again"]

        vote = await self.vote_manager.create_vote(title, ctx.author.id, ctx.guild.id, ctx.guild.icon)

        def response_check(message):
            return message.author.id == ctx.author.id and message.channel.id == ctx.channel.id

        msg = await ctx.send(content=f"```{msg_content[0]}\n{msg_content[1]}```")
        vote.setup_message = msg
        try:
            # role_msg = await self.bot.wait_for('message', check=response_check, timeout=60.0)
            role_msg = await self.wait_for_message(self.bot, ctx, timeout=60.0, check=response_check)
            if not role_msg:
                raise self.TimeoutError("Vote creation timed out")
            if role_msg.role_mentions:
                vote.add_roles(role_msg.role_mentions)
                roles_used = msg_content[2] + "\n" + (', '.join(role.name for role in role_msg.role_mentions))
            else:
                roles_used = "No roles selected."
            server_vcs = {}
            for x, vc in enumerate(ctx.guild.voice_channels):
                server_vcs[x] = vc
            vc_list = '\n'.join([f"{x}: {y.name}" for x, y in server_vcs.items()])
            await msg.edit(
                content=f"```{msg_content[0]}\n{roles_used}\n\n{msg_content[3]}\n{vc_list}\n{msg_content[4]}```")
            try:
                await role_msg.delete()
            except discord.errors.Forbidden:
                pass
            vc_msg = await self.wait_for_message(self.bot, ctx, timeout=60.0, check=response_check)
            if not vc_msg:
                raise self.TimeoutError("Vote creation timed out")
            if vc_msg.content != "no":
                channel = server_vcs[int(vc_msg.content)]
                vote.add_channel(channel.id)
                vc_used = msg_content[5] + channel.name
            else:
                vc_used = "No voice channel selected."

            await msg.edit(
                content=f"```{msg_content[0]}\n\n{roles_used}\n\n{vc_used}\n\n{msg_content[6]}\n{msg_content[7]}```")
            try:
                await vc_msg.delete()
            except discord.errors.Forbidden:
                pass

            chair_msg = await self.wait_for_message(self.bot, ctx, timeout=60.0, check=response_check)
            if not chair_msg:
                raise self.TimeoutError("Vote creation timed out")
            if chair_msg.content != "no" and chair_msg.mentions:
                vote.add_chair(chair_msg.mentions[0].id)
                chair_used = msg_content[8] + chair_msg.mentions[0].name
            else:
                vote.add_chair(ctx.author.id)
                chair_used = msg_content[8] + ctx.author.name

            embed = vote.create_voting_embed()
            await msg.edit(content=f"```{roles_used}\n\n{vc_used}\n\n{chair_used}\n\n{msg_content[9]}```", embed=embed)
            try:
                await chair_msg.delete()
            except discord.errors.Forbidden:
                pass

            vote.setup = True

        except (KeyError, ValueError):
            await msg.edit("```Vote was cancelled due to invalid response.```")
            self.vote_manager.remove_vote(ctx.author.id)
        except asyncio.TimeoutError:
            await msg.edit("```Vote was cancelled due to timeout.```")
            self.vote_manager.remove_vote(ctx.author.id)

    @is_vote_caller()
    @vote.command(name="addOption", brief="Add an option to an existing vote.")
    async def addOption(self, ctx, *, options_string):
        """
        Add an option to an existing vote. Separate the header and the body with a "+".
        :param options_string: the heading and body of the vote option being added
        :return:
        """
        vote = self.vote_manager.active_votes[ctx.author.id]
        if len(vote.options) > 9:
            raise self.OptionsError("The maximum number of options has been added")
        if len(options_string) > 600:
            raise self.OptionsError("Parameter too long, please use smaller options")
        header, body = options_string.split("+")
        vote.add_option({"header": header, "body": body})
        embed = vote.create_voting_embed()
        await vote.setup_message.edit(embed=embed)
        await ctx.message.delete()

    @is_vote_caller()
    @vote.command(name="cancel", brief="Cancel the vote creation process.")
    async def cancel(self, ctx):
        """
        Cancel the vote creation process.
        :param ctx:
        :return:
        """
        self.vote_manager.remove_vote(ctx.author.id)
        await ctx.send("Your active vote has been cancelled")

    @is_vote_caller()
    @vote.command(name="send", brief="Send the vote out to the specified group of users.")
    async def send(self, ctx):
        """
        Send the vote out to the specified group of users.
        :return:
        """
        vote = self.vote_manager.active_votes[ctx.author.id]
        if len(vote.options) < 2:
            raise self.OptionsError(f"Not enough options. Please add options using {KoalaBot.COMMAND_PREFIX}vote addOption")
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
                msg = await user.send(
                    "You have been asked to participate in this vote. Please react to make your choice.\n"
                    "You can change your mind until the vote is closed.\n"
                    "If you react multiple times it will take the lowest number you have reacted with.",
                    embed=vote.create_voting_embed())
                vote.register_send(msg.id, user.id)
                await vote.add_reactions(msg)
        await ctx.send(f"This vote has been sent out to {len(users)} people")

    @is_vote_caller()
    @vote.command(name="check", brief="Check the results of the vote without closing it.")
    async def check(self, ctx):
        """
        Check the results of the vote without closing it.
        :return:
        """
        embed = await self.make_result_embed(ctx)
        await ctx.send(embed=embed)

    @is_vote_caller()
    @vote.command(name="close")
    async def close(self, ctx):
        """
        Gather the results of the vote and close it.
        :return:
        """
        vote = self.vote_manager.active_votes[ctx.author.id]
        chair = await vote.get_chair(self.bot)
        embed = await self.make_result_embed(ctx)
        if chair:
            await chair.send(embed=embed)
            await ctx.send(f"Results have been sent to {chair}")
        await ctx.send(embed=embed)
        self.vote_manager.remove_vote(ctx.author.id)

    async def make_result_embed(self, ctx):
        """
        Automates creation of the result embed
        :param ctx: context of discord message
        :return:
        """
        vote = self.vote_manager.active_votes[ctx.author.id]
        results = await vote.get_results(self.bot)
        embed = discord.Embed(title=f"{vote.title} Results:")
        embed.set_thumbnail(url=vote.image)
        for opt in results:
            embed.add_field(name=opt["header"], value=f"{opt['count']} votes", inline=False)
        if not results:
            embed.add_field(name="No votes yet!", value="Try giving more time to vote")
        return embed

    async def update_vote_message(self, payload):
        """
        Updates the vote message with the currently selected option
        :param payload: the reaction event raw payload
        :return:
        """
        vote = self.vote_manager.get_sent_to(payload.message_id)
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
                embed.set_footer(text=f"You have chosen {choice.emoji}")
            else:
                embed.set_footer(text="There are no valid choices selected")
            await msg.edit(embed=embed)

    class OptionsError(Exception):
        pass

    class TimeoutError(Exception):
        pass


class VoteManager:
    """
    Wrapper for active votes with some utility functions.
    """
    def __init__(self):
        self.active_votes = {}

    async def create_vote(self, title, vote_id, guild_id, guild_pic):
        self.active_votes[vote_id] = Vote(title, vote_id, guild_id, guild_pic)
        return self.active_votes[vote_id]

    def remove_vote(self, vote_id):
        self.active_votes.pop(vote_id, None)

    def vote_exists(self, vote_id):
        return vote_id in self.active_votes.keys() and self.active_votes[vote_id].setup

    def get_sent_to(self, message_id):
        for vote in self.active_votes.values():
            if message_id in vote.sent_to.values():
                return vote
        return None


class Vote:
    """
    A vote object.
    """
    def __init__(self, title, vote_id: int, target_server: int, guild_pic: str):
        self.vote_start_time = time.time()
        self.target_server = target_server
        self.setup = False
        self.id = vote_id
        self.chair = 0
        self.target_roles = []
        self.target_voice_channel = 0
        self.title = title
        self.options = []
        self.sent_to = {}
        self.setup_message = None
        self.image = f"https://cdn.discordapp.com/icons/{self.target_server}/{guild_pic}.webp"

    def add_roles(self, roles):
        self.target_roles += roles

    def add_channel(self, channel_id):
        self.target_voice_channel = channel_id

    def add_chair(self, user_id):
        self.chair = user_id

    def add_option(self, options):
        option_id = len(self.options) + 1
        options["id"] = option_id
        self.options.append(options)

    def create_voting_embed(self):
        embed = discord.Embed(title=self.title)
        embed.set_thumbnail(url=self.image)
        for option in self.options:
            embed.add_field(name=f'{option["id"]} - {option["header"]}', value=option["body"], inline=False)
        return embed

    def register_send(self, msg_id, user_id):
        self.sent_to[user_id] = msg_id

    async def get_results(self, bot):
        results = {}
        for user_id, msg_id in self.sent_to.items():
            user = bot.get_user(user_id)
            msg = await user.fetch_message(msg_id)
            for reaction in msg.reactions:
                if reaction.count > 1:
                    if reaction.emoji in results.keys():
                        results[reaction.emoji] += 1
                    else:
                        results[reaction.emoji] = 1
                    break
        results_list = []
        for k, count in results.items():
            opt = self.get_opt_from_id(reverse_reference[k])
            opt["count"] = count
            results_list.append(opt)
        return results_list

    def get_opt_from_id(self, opt_id):
        for opt in self.options:
            if opt["id"] == opt_id:
                return opt

    async def add_reactions(self, msg):
        for option in self.options:
            await msg.add_reaction(emote_reference[option["id"]])

    async def get_chair(self, bot):
        if self.chair:
            return bot.get_user(self.chair)
        else:
            return None


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(Voting(bot))
    print("Voting is ready.")
