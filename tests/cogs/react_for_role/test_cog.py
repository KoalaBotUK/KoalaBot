#!/usr/bin/env python

"""
Testing KoalaBot ReactForRole Cog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import random

# Libs
import aiohttp
import discord
import discord.ext.test as dpytest
import mock
import pytest
from discord.ext import commands
from discord.ext.test import factories as dpyfactory

# Own modules
from koala.cogs.react_for_role import core
import koalabot
from koala.colours import KOALA_GREEN
from koala.db import session_manager
from tests.tests_utils import utils as testutils
from .utils import DBManager, independent_get_guild_rfr_message, independent_get_guild_rfr_required_role
from tests.log import logger
from koala.cogs import ReactForRole

# Constants

# Variables

@pytest.mark.asyncio
async def test_get_rfr_message_from_prompts(bot, utils_cog, rfr_cog):
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = bot.guilds[0]
    channel: discord.TextChannel = guild.channels[0]
    member: discord.Member = bot.guilds[0].members[0]
    msg: discord.Message = dpytest.back.make_message(".", member, channel)
    channel_id = msg.channel.id
    msg_id = msg.id

    await dpytest.message(koalabot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    with mock.patch('koala.cogs.ReactForRole.prompt_for_input',
                    side_effect=[str(channel_id), str(546542131)]) as mock_input:
        with mock.patch('discord.abc.Messageable.fetch_message', mock.AsyncMock(return_value=None)):
            with pytest.raises(commands.CommandError) as exc:
                await rfr_cog.get_rfr_message_from_prompts(ctx)
            assert str(exc.value) == "Invalid Message ID given."
    with mock.patch('koala.cogs.ReactForRole.prompt_for_input',
                    side_effect=[str(channel_id), str(msg_id)]) as mock_input:
        with mock.patch('discord.abc.Messageable.fetch_message', mock.AsyncMock(return_value=msg)):
            with pytest.raises(commands.CommandError) as exc:
                await rfr_cog.get_rfr_message_from_prompts(ctx)
            assert str(
                exc.value) == "Message ID given is not that of a react for role message."
    DBManager.add_rfr_message(msg.guild.id, channel_id, msg_id)
    with mock.patch('koala.cogs.ReactForRole.prompt_for_input',
                    side_effect=[str(channel_id), str(msg_id)]) as mock_input:
        with mock.patch('discord.abc.Messageable.fetch_message', mock.AsyncMock(return_value=msg)):
            rfr_msg, rfr_msg_channel = await rfr_cog.get_rfr_message_from_prompts(ctx)
            assert rfr_msg.id == msg.id
            assert rfr_msg_channel.id == channel_id


# TODO Actually implement the test.
@pytest.mark.parametrize("num_rows", [0, 1, 2, 20, 100, 250])
@pytest.mark.asyncio
async def test_parse_emoji_and_role_input_str(num_rows, utils_cog, rfr_cog):
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    await dpytest.message(koalabot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    for i in range(5):
        input_str = ""
        expected_emoji_list = []
        expected_role_list = []
        for j in range(num_rows):
            fake_emoji = random.choice(
                [testutils.fake_guild_emoji(guild), testutils.fake_unicode_emoji()])
            expected_emoji_list.append(str(fake_emoji))
            if isinstance(fake_emoji, discord.Emoji):
                fake_emoji_str = random.choice(
                    [fake_emoji.id, fake_emoji.name])
            else:
                fake_emoji_str = fake_emoji
            fake_role = testutils.fake_guild_role(guild)
            expected_role_list.append(fake_role)
            fake_role_str = random.choice([fake_role.id, fake_role.name,
                                           fake_role.mention])
            input_str += f"{fake_emoji_str}, {fake_role_str}\n\r"
        emoji_roles_list = await rfr_cog.parse_emoji_and_role_input_str(ctx, input_str, 20)
        for emoji_role in emoji_roles_list:
            assert str(emoji_role[0]) == str(
                expected_emoji_list[emoji_roles_list.index(emoji_role)])
            assert emoji_role[1] == expected_role_list[emoji_roles_list.index(
                emoji_role)]


@pytest.mark.skip("dpytest has non-implemented functionality for construction of guild custom emojis")
@pytest.mark.parametrize("num_rows", [0, 1, 2, 20])
@pytest.mark.asyncio
async def test_parse_emoji_or_roles_input_str(num_rows, utils_cog, rfr_cog):
    import emoji
    image = discord.File("utils/discord.png", filename="discord.png")
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    await dpytest.message(koalabot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    input_str = ""
    expected_list = []
    for j in range(num_rows):
        if random.choice([True, False]):
            if random.choice([True, False]):
                fake_emoji = testutils.fake_emoji_unicode()
                input_str += fake_emoji + "\n\r"
                expected_list.append(fake_emoji)
                logger.debug(f"Unicode emoji {j} in test {num_rows}: {emoji.emojize(fake_emoji)}")
            else:
                fake_emoji_name = testutils.fake_custom_emoji_name_str()
                fake_emoji = await guild.create_custom_emoji(name=fake_emoji_name, image=testutils.random_image())
                expected_list.append(fake_emoji)
                input_str += str(fake_emoji) + "\n\r"
                logger.debug(f"Custom emoji {j} in test {num_rows}: {str(fake_emoji)}")
        else:
            role_name = testutils.fake_custom_emoji_name_str()
            await guild.create_role(name=role_name, mentionable=True, hoist=True)
            fake_role: discord.Role = discord.utils.get(guild.roles, name=role_name)
            expected_list.append(fake_role)
            role_str = str(random.choice([fake_role.name, fake_role.id, fake_role.mention]))
            input_str += role_str + "\n\r"
            logger.debug(f"Role {j} in test {num_rows}: {fake_role}")

    logger.debug(f"Test {num_rows} input_str")
    logger.debug(input_str)
    result_list = await rfr_cog.parse_emoji_or_roles_input_str(ctx, input_str)
    for k in range(len(expected_list)):
        assert str(expected_list[k]) == str(result_list[k])


@pytest.mark.parametrize("msg_content", [None, "", "something", " "])
@pytest.mark.asyncio
async def test_prompt_for_input_str(msg_content, utils_cog, rfr_cog):
    config: dpytest.RunnerConfig = dpytest.get_config()
    author: discord.Member = config.members[0]
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    await dpytest.message(koalabot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    await dpytest.empty_queue()
    if not msg_content:
        with mock.patch('discord.client.Client.wait_for',
                        mock.AsyncMock(return_value=None)):
            result = await rfr_cog.prompt_for_input(ctx, "test")
            assert dpytest.verify().message().content(
                "Please enter test so I can progress further. I'll wait 60 seconds, don't worry.")
            assert dpytest.verify().message().content("Okay, I'll cancel the command.")
            assert not result
    else:
        msg: discord.Message = dpytest.back.make_message(content=msg_content, author=author, channel=channel)
        with mock.patch('discord.client.Client.wait_for',
                        mock.AsyncMock(return_value=msg)):
            result = await rfr_cog.prompt_for_input(ctx, "test")
            assert dpytest.verify().message().content(
                "Please enter test so I can progress further. I'll wait 60 seconds, don't worry.")
            assert result == msg_content


@pytest.mark.asyncio
async def test_prompt_for_input_attachment(rfr_cog, utils_cog):
    config: dpytest.RunnerConfig = dpytest.get_config()
    author: discord.Member = config.members[0]
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    await dpytest.message(koalabot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    await dpytest.empty_queue()
    attach: discord.Attachment = discord.Attachment(state=dpytest.back.get_state(),
                                                    data=dpytest.back.facts.make_attachment_dict("test.jpg", 15112122,
                                                                                                 "https://media.discordapp.net/attachments/some_number/random_number/test.jpg",
                                                                                                 "https://media.discordapp.net/attachments/some_number/random_number/test.jpg",
                                                                                                 height=1000,
                                                                                                 width=1000))
    message_dict = dpytest.back.facts.make_message_dict(channel, author, attachments=[attach])
    message: discord.Message = discord.Message(state=dpytest.back.get_state(), channel=channel, data=message_dict)
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=message)):
        result = await rfr_cog.prompt_for_input(ctx, "test")
        assert dpytest.verify().message().content(
            "Please enter test so I can progress further. I'll wait 60 seconds, don't worry.")
        assert isinstance(result, discord.Attachment)
        assert result.url == attach.url


@pytest.mark.asyncio
async def test_setup_rfr_reaction_permissions(rfr_cog):
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    bot: discord.Client = config.client
    with mock.patch('discord.ext.test.backend.FakeHttp.edit_channel_permissions') as mock_edit_channel_perms:
        for i in range(15):
            await guild.create_role(name=f"TestRole{i}", permissions=discord.Permissions.all())
        role: discord.Role = discord.utils.get(guild.roles, id=guild.id)
        # await core.setup_rfr_reaction_permissions(guild, channel, bot)
        await rfr_cog.overwrite_channel_add_reaction_perms(guild, channel)
        calls = [mock.call(channel.id, role.id, 0, 64, 'role', reason=None),
                 mock.call(channel.id, config.client.user.id, 64, 0, 'member',
                           reason=None)]  # assert it's called the role perms change first, then the member change
        mock_edit_channel_perms.assert_has_calls(calls)


@pytest.mark.asyncio
async def test_is_user_alive(utils_cog, rfr_cog):
    await dpytest.message(koalabot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value=None)):
        alive: bool = await rfr_cog.is_user_alive(ctx)
        assert not alive
    with mock.patch('discord.client.Client.wait_for',
                    mock.AsyncMock(return_value="a")):
        alive: bool = await rfr_cog.is_user_alive(ctx)
        assert alive


@pytest.mark.asyncio
async def test_get_embed_from_message(rfr_cog, bot: commands.Bot):
    config: dpytest.RunnerConfig = dpytest.get_config()
    author: discord.Member = config.members[0]
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    embed = discord.Embed(title="title", description="descr", type="rich", url="https://www.google.com")
    await channel.send(embed=embed)
    sent_msg: discord.Message = await dpytest.sent_queue.get()
    msg_mock: discord.Message = dpytest.back.make_message('a', author, channel)
    result = core.get_embed_from_message(None)
    assert result is None
    result = core.get_embed_from_message(msg_mock)
    assert result is None
    result = core.get_embed_from_message(sent_msg)
    assert dpytest.embed_eq(result, sent_msg.embeds[0])


@pytest.mark.asyncio
async def test_get_number_of_embed_fields(rfr_cog):
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    test_embed_dict: dict = {'title': 'title', 'description': 'descr', 'type': 'rich', 'url': 'https://www.google.com'}
    bot: discord.Client = config.client
    await bot.http.send_message(channel.id, '', embed=test_embed_dict)
    sent_msg: discord.Message = await dpytest.sent_queue.get()
    test_embed: discord.Embed = sent_msg.embeds[0]
    num_fields = 0
    for i in range(20):
        test_embed.add_field(name=f'field{i}', value=f'num{i}')
        num_fields += 1
        assert core.get_number_of_embed_fields(embed=test_embed) == num_fields


@pytest.mark.skip('dpytest currently has non-implemented functionality for construction of guild custom emojis')
@pytest.mark.asyncio
async def test_get_first_emoji_from_str(bot, utils_cog, rfr_cog):
    await dpytest.message(koalabot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    guild_emoji = testutils.fake_guild_emoji(guild)
    guild_emoji = discord.Emoji(guild=guild, state=None,
                                data={'name': "AAA", 'image': None, 'id': dpyfactory.make_id(),
                                      'require_colons': True, 'managed': False})
    guild._state.store_emoji(guild=guild,
                             data={'name': "AAA", 'image': None, 'id': dpyfactory.make_id(),
                                   'require_colons': True, 'managed': False})
    assert guild_emoji in guild.emojis

    author: discord.Member = config.members[0]
    channel: discord.TextChannel = guild.text_channels[0]
    msg: discord.Message = dpytest.back.make_message(str(guild_emoji), author, channel)
    result = await core.get_first_emoji_from_str(bot, guild, msg.content)
    logger.debug(result)
    assert isinstance(result, discord.Emoji), msg.content
    assert guild_emoji == result


@pytest.mark.asyncio
async def test_rfr_create_message(bot):
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    embed_channel: discord.TextChannel = dpytest.back.make_text_channel('EmbedChannel', guild)
    author: discord.Member = config.members[0]
    test_embed = discord.Embed(title="React for Role", description="Roles below!", colour=KOALA_GREEN)
    test_embed.set_footer(text="ReactForRole")
    test_embed.set_thumbnail(
        url=koalabot.KOALA_IMAGE_URL)
    with mock.patch('koala.cogs.ReactForRole.prompt_for_input',
                    mock.AsyncMock(return_value=embed_channel.mention)):
        with mock.patch('discord.client.Client.wait_for',
                        mock.AsyncMock(return_value=None)):
            with mock.patch('koala.cogs.ReactForRole.is_user_alive', mock.AsyncMock(return_value=True)):
                with mock.patch(
                        'koala.cogs.ReactForRole.overwrite_channel_add_reaction_perms') as mock_edit_channel_perms:
                    with mock.patch('discord.Message.delete') as mock_delete:
                        await dpytest.message(koalabot.COMMAND_PREFIX + "rfr createMessage")
                        mock_edit_channel_perms.assert_called_once_with(guild, embed_channel)
                        assert dpytest.verify().message().content(
                            "Okay, this will create a new react for role message in a channel of your choice."
                            "\nNote: The channel you specify will have its permissions edited to make it such that the "
                            "@ everyone role is unable to add new reactions to messages, they can only reaction with "
                            "existing ones. Please keep this in mind, or setup another channel entirely for this.")
                        assert dpytest.verify().message().content("This should be a thing sent in the right channel.")
                        assert dpytest.verify().message().content(
                            "Okay, what would you like the title of the react for role message to be? Please enter within 60 seconds.")
                        assert dpytest.verify().message().content(
                            "Okay, didn't receive a title. Do you actually want to continue? Send anything to confirm this.")
                        assert dpytest.verify().message().content(
                            "Okay, I'll just put in a default value for you, you can edit it later by using the k!rfr edit commands.")
                        assert dpytest.verify().message().content(
                            "Okay, the title of the message will be \"React for Role\". What do you want the description to be? I'll wait 60 seconds, don't worry")
                        assert dpytest.verify().message().content(
                            "Okay, didn't receive a description. Do you actually want to continue? Send anything to confirm this.")
                        assert dpytest.verify().message().content(
                            "Okay, I'll just put in a default value for you, you can edit it later by using the k!rfr edit command.")
                        assert dpytest.verify().message().content(
                            "Okay, the description of the message will be \"Roles below!\".\n Okay, I'll create the react for role message now.")
                        assert dpytest.verify().message()
                        msg = dpytest.sent_queue.get_nowait()
                        assert "You can use the other k!rfr subcommands to change the message and add functionality as required." in msg.content
                        mock_delete.assert_called_once()


@pytest.mark.asyncio
async def test_rfr_delete_message():
    with session_manager() as session:
        config: dpytest.RunnerConfig = dpytest.get_config()
        guild: discord.Guild = config.guilds[0]
        channel: discord.TextChannel = guild.text_channels[0]
        message: discord.Message = await dpytest.message("rfr")
        msg_id = message.id
        DBManager.add_rfr_message(guild.id, channel.id, msg_id)
        await dpytest.empty_queue()
        with mock.patch('koala.cogs.ReactForRole.get_rfr_message_from_prompts',
                        mock.AsyncMock(return_value=(message, channel))):
            with mock.patch('koala.cogs.ReactForRole.prompt_for_input', mock.AsyncMock(return_value="Y")):
                with mock.patch('discord.Message.delete') as mock_msg_delete:
                    await dpytest.message(koalabot.COMMAND_PREFIX + "rfr deleteMessage")
                    mock_msg_delete.assert_called_once()
                    assert dpytest.verify().message().content(
                        "Okay, this will delete an existing react for role message. I'll need some details first though.")
                    assert dpytest.verify().message()
                    assert dpytest.verify().message()
                    assert dpytest.verify().message()
                    assert not independent_get_guild_rfr_message(session, guild.id, channel.id, msg_id)


@pytest.mark.asyncio
async def test_rfr_edit_description():
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    embed: discord.Embed = discord.Embed(title="title", description="description")
    client: discord.Client = config.client
    message: discord.Message = await dpytest.message("rfr")
    msg_id = message.id
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    assert embed.description == 'description'
    with mock.patch('koala.cogs.ReactForRole.get_rfr_message_from_prompts',
                    mock.AsyncMock(return_value=(message, channel))):
        with mock.patch('koala.cogs.ReactForRole.prompt_for_input',
                        mock.AsyncMock(side_effect=["new description", "Y"])):
            with mock.patch('koala.cogs.react_for_role.core.get_embed_from_message', return_value=embed):
                await dpytest.message(koalabot.COMMAND_PREFIX + "rfr edit description")
                assert embed.description == 'new description'
                assert dpytest.verify().message()
                assert dpytest.verify().message()
                assert dpytest.verify().message()


@pytest.mark.asyncio
async def test_rfr_edit_title():
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    embed: discord.Embed = discord.Embed(title="title", description="description")
    client: discord.Client = config.client
    message: discord.Message = await dpytest.message("rfr")
    msg_id = message.id
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    assert embed.title == 'title'
    with mock.patch('koala.cogs.ReactForRole.get_rfr_message_from_prompts',
                    mock.AsyncMock(return_value=(message, channel))):
        with mock.patch('koala.cogs.ReactForRole.prompt_for_input',
                        mock.AsyncMock(side_effect=["new title", "Y"])):
            with mock.patch('koala.cogs.react_for_role.core.get_embed_from_message', return_value=embed):
                await dpytest.message(koalabot.COMMAND_PREFIX + "rfr edit title")
                assert embed.title == 'new title'
                assert dpytest.verify().message()
                assert dpytest.verify().message()
                assert dpytest.verify().message()


@pytest.mark.asyncio
async def test_rfr_edit_thumbnail_attach():
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    embed: discord.Embed = discord.Embed(title="title", description="description")
    embed.set_thumbnail(
        url="https://media.discordapp.net/attachments/611574654502699010/756152703801098280/IMG_20200917_150032.jpg")
    message: discord.Message = await dpytest.message("rfr")
    attach: discord.Attachment = discord.Attachment(state=dpytest.back.get_state(),
                                                    data=dpytest.back.facts.make_attachment_dict("test.jpg", -1,
                                                                                                 "https://media.discordapp.net/attachments/some_number/random_number/test.jpg",
                                                                                                 "https://media.discordapp.net/attachments/some_number/random_number/test.jpg",
                                                                                                 height=1000,
                                                                                                 width=1000,
                                                                                                 content_type="image/jpeg"))
    msg_id = message.id
    bad_attach = "something that's not an attachment"
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    assert embed.thumbnail.url == "https://media.discordapp.net/attachments/611574654502699010/756152703801098280/IMG_20200917_150032.jpg"

    with mock.patch('koala.cogs.ReactForRole.get_rfr_message_from_prompts',
                    mock.AsyncMock(return_value=(message, channel))):
        with mock.patch('koala.cogs.react_for_role.core.get_embed_from_message', return_value=embed):
            with mock.patch('koala.cogs.ReactForRole.prompt_for_input', return_value=attach):
                await dpytest.message("k!rfr edit image")
                assert embed.thumbnail.url == "https://media.discordapp.net/attachments/some_number/random_number/test.jpg"
            embed.set_thumbnail(
                url="https://media.discordapp.net/attachments/611574654502699010/756152703801098280/IMG_20200917_150032.jpg")


@pytest.mark.parametrize("attach", ["", "1", "not an attachment", "http://www.google.com", "https://www.google.com",
                                    "https://cdn.discordapp.com/attachments/734739036564095026/832375039650299954/9-24_EUW1-4321454326_01.webm"])
@pytest.mark.asyncio
async def test_rfr_edit_thumbnail_bad_attach(attach):
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    embed: discord.Embed = discord.Embed(title="title", description="description")
    embed.set_thumbnail(
        url="https://media.discordapp.net/attachments/611574654502699010/756152703801098280/IMG_20200917_150032.jpg")
    message: discord.Message = await dpytest.message("rfr")
    msg_id = message.id
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    assert embed.thumbnail.url == "https://media.discordapp.net/attachments/611574654502699010/756152703801098280/IMG_20200917_150032.jpg"

    with mock.patch('koala.cogs.ReactForRole.get_rfr_message_from_prompts',
                    mock.AsyncMock(return_value=(message, channel))):
        with mock.patch('koala.cogs.react_for_role.core.get_embed_from_message', return_value=embed):
            with mock.patch('koala.cogs.ReactForRole.prompt_for_input', return_value=attach):
                with pytest.raises((aiohttp.ClientError, aiohttp.InvalidURL, commands.BadArgument,
                                    commands.CommandInvokeError)) as exc:
                    await dpytest.message("k!rfr edit thumbnail")

                    assert embed.thumbnail.url == "https://media.discordapp.net/attachments/611574654502699010/756152703801098280/IMG_20200917_150032.jpg"


@pytest.mark.asyncio
@pytest.mark.parametrize("image_url", [
    "https://media.discordapp.net/attachments/611574654502699010/756152703801098280/IMG_20200917_150032.jpg",
    "https://images-ext-1.discordapp.net/external/to2H6kvblcjDUm5Smwx4rSqwCPTP-UDFdWp1ToEXJQM/https/cdn.weeb.sh/images/Hk9GpT_Pb.png?width=864&height=660",
    "https://cdn.weeb.sh/images/Hk9GpT_Pb.png",
    "https://cdn.discordapp.com/attachments/611574654502699010/828026462552457266/unknown.png"])
async def test_rfr_edit_thumbnail_links(image_url):
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    embed: discord.Embed = discord.Embed(title="title", description="description")
    embed.set_thumbnail(
        url="https://media.discordapp.net/attachments/611574654502699010/756152703801098280/IMG_20200917_150032.jpg")
    message: discord.Message = await dpytest.message("rfr")
    msg_id = message.id
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    assert embed.thumbnail.url == "https://media.discordapp.net/attachments/611574654502699010/756152703801098280/IMG_20200917_150032.jpg"

    with mock.patch('koala.cogs.ReactForRole.get_rfr_message_from_prompts',
                    mock.AsyncMock(return_value=(message, channel))):
        with mock.patch('koala.cogs.react_for_role.core.get_embed_from_message', return_value=embed):
            with mock.patch('koala.cogs.ReactForRole.prompt_for_input', return_value=image_url):
                assert embed.thumbnail.url == "https://media.discordapp.net/attachments/611574654502699010/756152703801098280/IMG_20200917_150032.jpg"
                await dpytest.message("k!rfr edit image")
                assert embed.thumbnail.url != "https://media.discordapp.net/attachments/611574654502699010/756152703801098280/IMG_20200917_150032.jpg"


@pytest.mark.skip("Unsupported API Calls")
@pytest.mark.parametrize("arg", ["Y", "N"])
@pytest.mark.asyncio
async def test_rfr_edit_inline_all(arg):
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    embed1: discord.Embed = discord.Embed(title="title", description="description")
    embed1.add_field(name="field1", value="value1", inline=True)
    embed2: discord.Embed = discord.Embed(title="title2", description="description2")
    embed2.add_field(name="field2", value="value2", inline=False)
    message1: discord.Message = await dpytest.message("rfr")
    message2: discord.Message = await dpytest.message("rfr")
    msg1_id = message1.id
    msg2_id = message2.id
    DBManager.add_rfr_message(guild.id, channel.id, msg1_id)
    DBManager.add_rfr_message(guild.id, channel.id, msg2_id)
    await dpytest.sent_queue.empty()
    calls = [mock.call(0, name="field1", value="value1", inline=(arg == "Y")),
             mock.call(0, name="field2", value="value2", inline=(arg == "Y"))]
    with mock.patch("koala.cogs.ReactForRole.prompt_for_input", side_effects=["all", arg]):
        with mock.patch("discord.abc.Messageable.fetch_message", side_effects=[message1, message2]):
            with mock.patch("koala.cogs.react_for_role.core.get_embed_from_message", side_effects=[embed1, embed2]):
                with mock.patch('discord.Embed.set_field_at') as mock_call:
                    await dpytest.message("k!rfr edit inline")
                    assert dpytest.verify().message()
                    assert dpytest.verify().message()
                    assert dpytest.verify().message().content(
                        "Keep in mind that this process may take a while if you have a lot of RFR messages on your server.")
                    assert dpytest.verify().message().content("Okay, the process should be finished now. Please check.")


@pytest.mark.skip("Unsupported API Calls")
async def test_rfr_edit_inline_specific():
    assert False


@pytest.mark.asyncio
async def test_rfr_add_roles_to_msg():
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    embed: discord.Embed = discord.Embed(title="title", description="description")
    client: discord.Client = config.client
    author: discord.Member = config.members[0]
    message: discord.Message = await dpytest.message("rfr")
    msg_id: int = message.id
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    input_em_ro_content = ""
    em_list = []
    ro_list = []
    for i in range(5):
        em = testutils.fake_unicode_emoji()
        ro = testutils.fake_guild_role(guild)
        input_em_ro_content += f"{str(em)}, {ro.id}\n\r"
        em_list.append(em)
        ro_list.append(ro.mention)
    input_em_ro_msg: discord.Message = dpytest.back.make_message(input_em_ro_content, author, channel)

    with mock.patch('koala.cogs.ReactForRole.get_rfr_message_from_prompts',
                    mock.AsyncMock(return_value=(message, channel))):
        with mock.patch('koala.cogs.react_for_role.core.get_embed_from_message', return_value=embed):
            with mock.patch('discord.client.Client.wait_for',
                            mock.AsyncMock(return_value=input_em_ro_msg)):
                with mock.patch('discord.Embed.add_field') as add_field:
                    await dpytest.message(koalabot.COMMAND_PREFIX + "rfr addRoles")
                    calls = []
                    for i in range(5):
                        calls.append(mock.call(name=str(em_list[i]), value=ro_list[i], inline=False))
                    add_field.has_calls(calls)


@pytest.mark.asyncio
async def test_rfr_remove_roles_from_msg():
    config: dpytest.RunnerConfig = dpytest.get_config()
    guild: discord.Guild = config.guilds[0]
    channel: discord.TextChannel = guild.text_channels[0]
    embed: discord.Embed = discord.Embed(title="title", description="description")
    author: discord.Member = config.members[0]
    message: discord.Message = await dpytest.message("rfr")
    msg_id: int = message.id
    DBManager.add_rfr_message(guild.id, channel.id, msg_id)
    input_em_ro_content = ""
    em_ro_list = []
    for i in range(5):
        em = testutils.fake_unicode_emoji()
        ro = testutils.fake_guild_role(guild)
        x = random.choice([str(em), str(ro.id)])
        input_em_ro_content += f"{x}\n\r"
        em_ro_list.append(x)
        embed.add_field(name=str(em), value=ro.mention, inline=False)
        DBManager.add_rfr_message_emoji_role(1, str(em), ro.id)

    input_em_ro_msg: discord.Message = dpytest.back.make_message(input_em_ro_content, author, channel)
    with mock.patch('koala.cogs.ReactForRole.get_rfr_message_from_prompts',
                    mock.AsyncMock(return_value=(message, channel))):
        with mock.patch('koala.cogs.react_for_role.core.get_embed_from_message', return_value=embed):
            with mock.patch('discord.client.Client.wait_for',
                            mock.AsyncMock(return_value=input_em_ro_msg)):
                with mock.patch('discord.Embed.add_field') as add_field:
                    with mock.patch(
                            'koala.cogs.react_for_role.db.ReactForRoleDBManager.remove_rfr_message_emoji_role') as remove_emoji_role:
                        add_field.reset_mock()
                        await dpytest.message(koalabot.COMMAND_PREFIX + "rfr removeRoles")
                        add_field.assert_not_called()
                        calls = []
                        for i in range(5):
                            calls.append((1, em_ro_list[i]))
                        remove_emoji_role.has_calls(calls)


# role-check tests
@pytest.mark.parametrize("num_roles, num_required",
                         [(0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2), (5, 1), (5, 2), (20, 5)])
@pytest.mark.asyncio
async def test_can_have_rfr_role(num_roles, num_required, rfr_cog):
    with session_manager() as session:
        config: dpytest.RunnerConfig = dpytest.get_config()
        guild: discord.Guild = config.guilds[0]
        r_list = []
        for i in range(num_roles):
            role = testutils.fake_guild_role(guild)
            r_list.append(role)
        required = random.sample(list(r_list), num_required)
        for r in required:
            DBManager.add_guild_rfr_required_role(guild.id, r.id)
            assert independent_get_guild_rfr_required_role(session, guild.id, r.id) is not None
        for i in range(num_roles):
            mem_roles = []
            member: discord.Member = await dpytest.member_join()
            for j in range(i):
                mem_roles.append(r_list[j])
                await member.add_roles(r_list[j])

            assert len(mem_roles) == i
            if len(required) == 0:
                assert rfr_cog.can_have_rfr_role(member)
            else:
                assert rfr_cog.can_have_rfr_role(member) == any(
                    x in required for x in member.roles), f"\n\r{member.roles}\n\r{required}"
