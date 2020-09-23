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

class Voting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vote_manager = VoteManager()

    @commands.command(name="startVote")
    async def startVote(self, ctx, *, title):
        if self.vote_manager.vote_exists(ctx.author.id):
            await ctx.send("You already have an active vote somewhere, please close it before trying to create a new one.")
            return

        await ctx.send(f"You have started making a vote titled {title}. Each upcoming prompt has a 60 second timeout.")
        self.vote_manager.create_vote(title, ctx.author.id)

        def response_check(message):
            return message.author.id == ctx.author.id and message.channel.id == ctx.channel.id

        try:
            await ctx.send(
                "```Do you want this vote to be sent to users with specific roles? If so ping each role you want (e.g. @student @staff). If no, reply 'no'.```")
            role_msg = await self.bot.wait_for('message', check=response_check, timeout=60.0)
            if role_msg.role_mentions:
                self.vote_manager.add_roles(ctx.author.id, role_msg.role_mentions)

            server_vcs = {}
            for x, vc in enumerate(ctx.guild.voice_channels):
                server_vcs[x] = vc
            vc_list = '\n'.join([f"{x}: {y.name}" for x, y in server_vcs.items()])
            vc_message_string = \
                f"""```
Do you want this vote to be sent to users in a specific voice channel? If so please respond with the corresponding number from this list:
{vc_list}
If not, reply 'no'.
```
"""
            await ctx.send(vc_message_string)
            vc_msg = await self.bot.wait_for('message', check=response_check, timeout=60.0)
            if vc_msg.content != "no":
                channel = server_vcs[int(vc_msg.content)]
                self.vote_manager.add_channel(ctx.author.id, channel.id)

            await ctx.send("```Do you want there to be a chair for this vote? (User will be sent vote results upon vote closure). Ping the user or reply 'no' for results to only be sent in channel where vote is closed.```")
            chair_msg = await self.bot.wait_for('message', check=response_check, timeout=60.0)
            if chair_msg.content != "no" and chair_msg.mentions:
                self.vote_manager.add_chair(ctx.author.id, chair_msg.mentions[0].id)
            await ctx.send(f"Vote creation is complete, please add options with {KoalaBot.COMMAND_PREFIX}addVoteOption, and send out vote with {KoalaBot.COMMAND_PREFIX}sendVote")
        except KeyError:
            await ctx.send("Vote was cancelled due to invalid response.")
            self.vote_manager.remove_vote(ctx.author.id)
        except ValueError:
            await ctx.send("Vote was cancelled due to invalid response.")
            self.vote_manager.remove_vote(ctx.author.id)
        except asyncio.TimeoutError:
            await ctx.send("Vote was cancelled due to timeout.")
            self.vote_manager.remove_vote(ctx.author.id)

    @commands.command(name="addVoteOption")
    async def addOption(self, ctx, *, options_string):
        header, body = options_string.split("+")
        self.vote_manager.add_option(ctx.author.id, {"header": header, "body": body})
        await ctx.send(f"Added option **{header}** with description **{body}**")

    @commands.command(name="previewVote")
    async def preview(self, ctx):
        msg = await ctx.send(embed=self.vote_manager.create_voting_embed(ctx.author.id))
        await self.vote_manager.add_reactions(ctx.author.id, msg)

    @commands.command(name="cancelVote")
    async def cancel(self, ctx):
        self.vote_manager.remove_vote(ctx.author.id)
        await ctx.send("Your active vote has been cancelled")

    @commands.command(name="sendVote")
    async def send(self, ctx):
        vote = self.vote_manager.active_votes[ctx.author.id]
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
            # if user is bot skip
            msg = await user.send("You have been asked to participate in this vote. Please react to make your choice. If you react multiple times it will take the lowest number you have reacted with.",
                                  embed=self.vote_manager.create_voting_embed(ctx.author.id))
            self.vote_manager.register_send(ctx.author.id, msg.id, user.id)
            await self.vote_manager.add_reactions(ctx.author.id, msg)
        await ctx.send(f"This vote has been sent out to {len(users)} people")

    @commands.command(name="closeVote")
    async def close(self, ctx):
        vote = self.vote_manager.active_votes[ctx.author.id]
        results = await self.vote_manager.get_results(self.bot, ctx.author.id)
        embed = discord.Embed(title=f"{vote.title} Results:")
        for opt in results:
            embed.add_field(name=opt["header"], value=f"{opt['count']} votes", inline=False)
        self.vote_manager.remove_vote(ctx.author.id)
        await ctx.send(embed=embed)


class VoteManager:
    def __init__(self):
        self.active_votes = {}

    def create_vote(self, title, vote_id):
        self.active_votes[vote_id] = Vote(title, vote_id)
        return self.active_votes[vote_id]

    def remove_vote(self, vote_id):
        self.active_votes.pop(vote_id, None)

    def add_roles(self, vote_id, roles):
        self.active_votes[vote_id].target_roles += roles

    def vote_exists(self, vote_id):
        return vote_id in self.active_votes.keys()

    def add_channel(self, vote_id, channel_id):
        self.active_votes[vote_id].target_voice_channel = channel_id

    def add_chair(self, vote_id, user_id):
        self.active_votes[vote_id].chair = user_id

    def add_option(self, vote_id, options):
        option_id = len(self.active_votes[vote_id].options) + 1
        options["id"] = option_id
        self.active_votes[vote_id].options.append(options)

    def create_voting_embed(self, vote_id):
        vote = self.active_votes[vote_id]
        embed = discord.Embed(title=vote.title)
        for option in vote.options:
            embed.add_field(name=f'{option["id"]} - {option["header"]}', value=option["body"], inline=False)
        return embed

    def register_send(self, vote_id, msg_id, user_id):
        self.active_votes[vote_id].sent_to[user_id] = msg_id

    def get_opt_from_id(self, vote_id, opt_id):
        for opt in self.active_votes[vote_id].options:
            if opt["id"] == opt_id:
                return opt

    async def get_results(self, bot, vote_id):
        vote = self.active_votes[vote_id]
        results = {}
        for user_id, msg_id in vote.sent_to.items():
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
            opt = self.get_opt_from_id(vote.id, reverse_reference[k])
            opt["count"] = count
            results_list.append(opt)
        return results_list

    async def add_reactions(self, vote_id, msg):
        for option in self.active_votes[vote_id].options:
            await msg.add_reaction(emote_reference[option["id"]])


class Vote:
    def __init__(self, title, vote_id: int):
        self.vote_start_time = time.time()
        self.id = vote_id
        self.chair = 0
        self.target_roles = []
        self.target_voice_channel = 0
        self.title = title
        self.vote_over = False
        self.options = []
        self.sent_to = {}


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(Voting(bot))
    print("Voting is ready.")
