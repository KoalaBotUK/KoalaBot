#!/usr/bin/env python

"""
Koala Bot Base Code

Commented using reStructuredText (reST)
"""
__author__ = "Jack Draper, Kieran Allinson, Viraj Shah"
__copyright__ = "Copyright (c) 2020 KoalaBot"
__credits__ = ["Jack Draper", "Kieran Allinson", "Viraj Shah"]
__license__ = "MIT License"
__version__ = "0.0.1"
__maintainer__ = "Jack Draper, Kieran Allinson, Viraj Shah"
__email__ = "koalabotuk@gmail.com"
__status__ = "Development"  # "Prototype", "Development", or "Production"

# Futures

# Built-in/Generic Imports
import os
import asyncio
import sys
from unittest import TestCase
import threading
import multiprocessing


# Libs
import discord
import distest
from dotenv import load_dotenv

# Own modules
import KoalaBot
from tests.utils.test_utils import assert_activity, run_bot, run_test_bot

# Constants
load_dotenv()
BOT_NAME = os.environ['DISCORD_NAME']
BOT_TEST_TOKEN = os.environ['DISCORD_TEST_TOKEN']
BOT_TOKEN = os.environ['DISCORD_TOKEN']


test_collector = distest.TestCollector()
# Variables


class Test(TestCase):

    def setUp(self):
        print("Test started")

    def test_on_ready(self):
        # KoalaBot.on_ready()
        # assert KoalaBot.started
        # print(KoalaBot.client.activity)
        assert True
        print("done")

    @test_collector()
    async def test_ping(self, interface):
        await interface.assert_reply_contains("ping?", "pong!")

    def test_playing_new_discord_activity(self):
        test_name = "Half Life 3"
        assert_activity(KoalaBot.new_discord_activity("playing", test_name),
                        type=discord.ActivityType.playing, name=test_name+KoalaBot.KOALA_PLUG)

    def test_watching_new_discord_activity(self):
        test_name = "you"
        assert_activity(KoalaBot.new_discord_activity("watching", test_name),
                        type=discord.ActivityType.watching, name=test_name+KoalaBot.KOALA_PLUG)

    def test_listening_new_discord_activity(self):
        test_name = "/Darude Sandstorm"
        assert_activity(KoalaBot.new_discord_activity("listening", test_name),
                        type=discord.ActivityType.listening, name=test_name+KoalaBot.KOALA_PLUG)

    def test_streaming_new_discord_activity(self):
        test_name = "__your room__"
        assert_activity(KoalaBot.new_discord_activity("streaming", test_name),
                        type=discord.ActivityType.streaming, name=test_name+KoalaBot.KOALA_PLUG,
                        url=KoalaBot.STREAMING_URL)

    def test_custom_new_discord_activity(self):
        test_name = "1 4M K04L4"
        assert_activity(KoalaBot.new_discord_activity("custom", test_name),
                        type=discord.ActivityType.custom, name=test_name+KoalaBot.KOALA_PLUG)

    def test_distests(self):
        # Starts bot using the given BOT_ID
        #loop = asyncio.get_event_loop()
        ##loop.create_task(KoalaBot.client.run(BOT_TOKEN))multiprocessing.Process
        print("Thread starting")
        thread = threading.Thread(target=run_bot, args=(KoalaBot, ))
        thread.start()
        #thread2 = multiprocessing.Process(target=run_test_bot, args=(distest, test_collector))
        print("Thread 1 started")
        distest.run_command_line_bot(BOT_NAME, BOT_TEST_TOKEN, "all", 729700330840915978, True, test_collector, 5)
        #thread2.start()
        print("Thread 2 started")
        # running_bot = Thread(KoalaBot.client.run(BOT_TOKEN))
        # running_bot.start()
        # sys.argv.append(BOT_NAME)
        # sys.argv.append(BOT_TEST_TOKEN)
        # sys.argv[2] = str(BOT_TEST_TOKEN)
        # distest.run_dtest_bot(sys.argv, test_collector)


    def tearDown(self):
        # KoalaBot.client.close()
        print("Test Complete")

