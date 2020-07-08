"""
A functional demo of all possible test cases. This is the format you will want to use with your testing bot.
    Run with:
        python example_tests.py TARGET_NAME TESTER_TOKEN
"""
import asyncio
import sys
import discord.ext.test as dpytest
import pytest
from discord import Embed
import os
import KoalaBot
from cogs import Greetings
from discord.ext import commands, tasks
import threading
from dotenv import load_dotenv
load_dotenv()
BOT_NAME = int(os.environ['DISCORD_NAME'])
BOT_TEST_TOKEN = os.environ['DISCORD_TEST_TOKEN']
BOT_TOKEN = os.environ['DISCORD_TOKEN']

# The tests themselves

#test_collector = TestCollector()
created_channel = None


@pytest.mark.asyncio
async def test_ping():
    bot = KoalaBot.client
    # thread = threading.Thread(target=KoalaBot.client.run, args=(BOT_TOKEN,))
    # Load any extensions/cogs you want to in here
    # thread.start()
    bot = commands.Bot(command_prefix="k!")
    bot.add_cog(Greetings.Greetings(bot))
    dpytest.configure(bot, 1, 1, 1)

    await dpytest.message("k!hi")
    dpytest.verify_message("i")
    # KoalaBot.client.run(BOT_TOKEN)

# Actually run the bot
"""
if __name__ == "__main__":
    test_ping()
    print("Thread starting")
    #thread = threading.Thread(target=KoalaBot.client.run, args=(BOT_TOKEN,))
     #thread.start()
    # thread2 = multiprocessing.Process(target=run_test_bot, args=(distest, test_collector))
    print(f"Thread 1 started {type(BOT_NAME)}")
    # thread2.start()
    #run_command_line_bot(BOT_NAME, BOT_TEST_TOKEN, "all", 729700330840915978, True, test_collector, 5)
    print("Thread 2 started")
"""