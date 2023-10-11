#!/usr/bin/env python

"""
Koala Bot Insights Core Code
"""
# Futures

# Built-in/Generic Imports

# Libs

# Own modules

# Constants

# Variables


def get_insights(bot):
    """
    Processes the information concerning the number of servers and members, and the formatting for insights
    :param bot: The bot for which information is being gathered
    """

    message = f"Insights:\nThis bot is in a total of {len(bot.guilds)} servers.\nThere are a total " +\
              f"of {sum([len(guild.members) for guild in bot.guilds])} members across these servers."

    return message


def get_servers(bot, filter_string):
    """
    Retrieves a list of servers that the bot is in, can also use a filter to select only servers containing that string
    :param bot: The bot for which information is being gathered
    :param filter_string: A filter string which allows only servers containing that string to be selected
    """

    if filter_string != "":
        server_list = [guild.name for guild in bot.guilds if filter_string.lower() in guild.name.lower()]
    else:
        server_list = [guild.name for guild in bot.guilds]

    return server_list
