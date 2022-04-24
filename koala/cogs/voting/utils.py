#!/usr/bin/env python

"""
Koala Bot Vote Cog code and additional base cog functions
Commented using reStructuredText (reST)
"""
# Built-in/Generic Imports

# Libs
import discord

# Own modules

# Constants
MIN_ID_VALUE = 100000000000000000
MAX_ID_VALUE = 999999999999999999

# Variables


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
