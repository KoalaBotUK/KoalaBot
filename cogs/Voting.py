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
            await ctx.send(f"Vote creation is complete, please add options with {KoalaBot.COMMAND_PREFIX}addOption, and send out vote with {KoalaBot.COMMAND_PREFIX}sendVote")
        except KeyError:
            await ctx.send("Vote was cancelled due to invalid response.")
            self.vote_manager.remove_vote(ctx.author.id)
        except ValueError:
            await ctx.send("Vote was cancelled due to invalid response.")
            self.vote_manager.remove_vote(ctx.author.id)
        except asyncio.TimeoutError:
            await ctx.send("Vote was cancelled due to timeout.")
            self.vote_manager.remove_vote(ctx.author.id)

    @commands.command(name="addOption")
    async def addOption(self, ctx, *, options_string):
        pass


class VoteManager:
    def __init__(self):
        self.active_votes = {}

    def create_vote(self, title, vote_id):
        self.active_votes[vote_id] = Vote(title, vote_id)
        return self.active_votes[vote_id]

    def remove_vote(self, vote_id):
        self.active_votes[vote_id] = None

    def add_roles(self, vote_id, roles):
        self.active_votes[vote_id].target_roles += roles

    def vote_exists(self, vote_id):
        return vote_id in self.active_votes.keys()

    def add_channel(self, vote_id, channel_id):
        self.active_votes[vote_id].target_voice_channel = channel_id

    def add_chair(self, vote_id, user_id):
        self.active_votes[vote_id].chair = user_id


class Vote:
    def __init__(self, title, vote_id: int):
        self.vote_start_time = time.time()
        self.id = vote_id
        self.chair = 0
        self.target_roles = []
        self.target_voice_channel = 0
        self.title = title
        self.vote_over = False


def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(Voting(bot))
    print("Voting is ready.")
