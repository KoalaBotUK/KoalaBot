#!/usr/bin/env python

"""
Testing KoalaBot BaseCog

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
from typing import List
import re
import mock
import asyncio
import random
# Libs
import discord.ext.test as dpytest

import pytest
from discord.ext import commands
import discord
# Own modules
import KoalaBot
from cogs import ColourRole
from cogs.ColourRole import ColourRoleDBManager
from utils.KoalaDBManager import KoalaDBManager
from tests.utils import TestUtilsCog

# Constants

# Variables
role_colour_cog: ColourRole.ColourRole = None
utils_cog: TestUtilsCog.TestUtilsCog = None
DBManager = ColourRoleDBManager(KoalaBot.database_manager)
DBManager.create_tables()


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global role_colour_cog
    global utils_cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    role_colour_cog = ColourRole.ColourRole(bot)
    utils_cog = TestUtilsCog.TestUtilsCog(bot)
    bot.add_cog(role_colour_cog)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    print("Tests starting")


async def make_list_of_roles(guild: discord.Guild, length: int) -> List[discord.Role]:
    arr: List[discord.Role] = []
    for i in range(length):
        role = await guild.create_role(name=f"TestRole{i}")
        arr.append(role)
        await arr[i].edit(position=i + 1)
    return arr


def random_colour_str():
    import random
    return hex(random.randint(0, 16777216))


def random_colour() -> discord.Colour:
    import random
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return discord.Colour.from_rgb(r, g, b)


def make_list_of_colours(num: int) -> List[discord.Colour]:
    arr: List[discord.Colour] = []
    for i in range(num):
        arr.append(random_colour())
    return arr


async def make_list_of_custom_colour_roles(guild: discord.Guild, length: int) -> List[discord.Role]:
    arr = []
    for i in range(length):
        role = await guild.create_role(name=f"KoalaBot[{random_colour_str().upper()}]", colour=random_colour())
        arr.append(role)
        await arr[i].edit(position=i + 1)
    return arr


async def make_list_of_protected_colour_roles(guild: discord.Guild, length: int) -> List[discord.Role]:
    arr = []
    for i in range(length):
        role = await guild.create_role(name=f"TestProtectedRole{i}", colour=random_colour())
        arr.append(role)
        await arr[i].edit(position=i + 1)
        DBManager.add_guild_protected_colour_role(guild.id, role.id)
    return arr


def independent_get_protected_colours(guild_id):
    dbm: KoalaDBManager = KoalaBot.database_manager
    rows = dbm.db_execute_select(f"""SELECT * FROM GuildInvalidCustomColourRoles WHERE guild_id = {guild_id};""")
    if not rows:
        return []
    return [row[1] for row in rows]


def independent_get_colour_change_roles(guild_id):
    dbm: KoalaDBManager = KoalaBot.database_manager
    rows = dbm.db_execute_select(f"""SELECT * FROM GuildColourChangePermissions WHERE guild_id = {guild_id};""")
    if not rows:
        return []
    return [row[1] for row in rows]


@pytest.mark.parametrize("length", [0, 1, 2, 5])
@pytest.mark.asyncio
async def test_cr_db_functions_protected_colour_roles(length):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role_list = await make_list_of_roles(guild, length)
    # Test dbmanager add protected role
    for role in role_list:
        DBManager.add_guild_protected_colour_role(guild.id, role.id)
    protected_role_list = independent_get_protected_colours(guild.id)
    assert protected_role_list == [protected_role.id for protected_role in role_list], [guild_role.id for guild_role in
                                                                                        guild.roles]
    # Test dbmanager get protected roles
    db_get_list = DBManager.get_protected_colour_roles(guild.id)
    assert set(protected_role_list) == set(db_get_list)
    # Test dbmanager remove protected role and teardown test
    for role in role_list:
        DBManager.remove_guild_protected_colour_role(guild.id, role.id)
    assert independent_get_protected_colours(guild.id) == []


@pytest.mark.parametrize("length", [0, 1, 2, 5])
@pytest.mark.asyncio
async def test_cr_db_functions_colour_change_roles(length):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role_list = await make_list_of_roles(guild, length)
    # Test dbmanager add colour change role
    for role in role_list:
        DBManager.add_colour_change_role_perms(guild.id, role.id)
    colour_change_role_list = independent_get_colour_change_roles(guild.id)
    assert colour_change_role_list == [colour_change_role.id for colour_change_role in role_list], [guild_role.id for
                                                                                                    guild_role in
                                                                                                    guild.roles]
    # Test dbmanager get colour change roles
    db_get_list = DBManager.get_colour_change_roles(guild.id)
    assert set(colour_change_role_list) == set(db_get_list)
    # Test dbmanager remove colour change role and teardown test
    for role in role_list:
        DBManager.remove_colour_change_role_perms(guild.id, role.id)
    assert independent_get_colour_change_roles(guild.id) == []


@pytest.mark.asyncio
async def test_is_allowed_to_change_colour_no_guild_roles():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    assert not ColourRole.is_allowed_to_change_colour(ctx)


@pytest.mark.asyncio
async def test_is_allowed_to_change_colour_false():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    roles = await make_list_of_roles(ctx.guild, 1)
    role = roles[0]
    DBManager.add_colour_change_role_perms(ctx.guild.id, role.id)
    assert not ColourRole.is_allowed_to_change_colour(ctx)


@pytest.mark.asyncio
async def test_is_allowed_to_change_colour_true():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    roles = await make_list_of_roles(ctx.guild, 1)
    role = roles[0]
    member: discord.Member = ctx.author
    DBManager.add_colour_change_role_perms(ctx.guild.id, role.id)
    await member.add_roles(role)
    assert ColourRole.is_allowed_to_change_colour(ctx)


@pytest.mark.parametrize("hex_str, value",
                         [("000000", 0), ("111111", 1118481), ("228822", 2263074), ("ff82ae", 16745134)])
@pytest.mark.asyncio
async def test_get_colour_from_hex_str(hex_str, value):
    colour: discord.Colour = role_colour_cog.get_colour_from_hex_str(hex_str)
    assert colour.value == value, str(colour.r) + " " + str(colour.g) + " " + str(colour.b) + " " + str(colour.value)


@pytest.mark.asyncio
@pytest.mark.parametrize("colour_str, expected",
                         [("", False), (".", False), (" ", False), ("223", False), ("a", False), ("ffgeaa", False),
                          ("FFeehu", False), ("FFee66", True), ("ffeea7", True), ("ABCDEF", True)])
async def test_is_valid_colour_str(colour_str, expected):
    assert role_colour_cog.is_valid_colour_str(colour_str.upper()) == expected


@pytest.mark.parametrize("colour1_str, colour2_str, expected",
                         [("ffffff", "ffffff", 0), ("FFFFFF", "ffffff", 0), ("ffffff", "000000", 764.8339663572415),
                          ("ff74aa", "6900ff", 362.23060571789074), ("223636", "363636", 29.47456530637899)])
@pytest.mark.asyncio
async def test_get_rgb_colour_distance(colour1_str, colour2_str, expected):
    colour1 = role_colour_cog.get_colour_from_hex_str(colour1_str)
    colour2 = role_colour_cog.get_colour_from_hex_str(colour2_str)
    dist = role_colour_cog.get_rgb_colour_distance(colour1, colour2)
    assert dist == expected


@pytest.mark.asyncio
async def test_role_already_exists():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    role_exists = role_colour_cog.role_already_exists(ctx, "ffae14")
    assert not role_exists
    await guild.create_role(name="KoalaBot[0xffae14]")
    role_exists = role_colour_cog.role_already_exists(ctx, "ffae14")
    assert role_exists


@pytest.mark.parametrize("num_roles", [0, 1, 2, 5])
@pytest.mark.asyncio
async def test_get_protected_roles(num_roles):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    roles = await make_list_of_roles(guild, num_roles)
    for role in roles:
        DBManager.add_guild_protected_colour_role(guild.id, role.id)
    return_roles = role_colour_cog.get_protected_roles(guild)
    assert set(roles) == set(return_roles)


@pytest.mark.parametrize("num_roles", [0, 1, 2, 5])
@pytest.mark.asyncio
async def test_get_custom_colour_allowed_roles(num_roles):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    roles = await make_list_of_roles(guild, num_roles)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    for role in roles:
        DBManager.add_colour_change_role_perms(guild.id, role.id)
    return_roles = role_colour_cog.get_custom_colour_allowed_roles(ctx)
    assert set(roles) == set(return_roles)


@pytest.mark.parametrize("num_roles", [0, 1, 2, 5])
@pytest.mark.asyncio
async def test_prune_guild_empty_colour_roles(num_roles):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    roles = await make_list_of_custom_colour_roles(guild, num_roles)
    assert set(roles).issubset(guild.roles)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    await role_colour_cog.prune_guild_empty_colour_roles(ctx)
    assert not any(roles) in guild.roles


@pytest.mark.parametrize("num_roles", [0, 1, 2, 5])
@pytest.mark.asyncio
async def test_prune_author_old_colour_roles(num_roles):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    roles = await make_list_of_custom_colour_roles(guild, num_roles)
    assert set(roles).issubset(guild.roles)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    await role_colour_cog.prune_author_old_colour_roles(ctx)
    author: discord.Member = ctx.author
    assert not any(roles) in author.roles


@pytest.mark.parametrize("num_roles", [0, 1, 2, 5])
@pytest.mark.asyncio
async def test_calculate_custom_colour_role_position(num_roles):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    roles = await make_list_of_roles(guild, 5)
    # add num_roles roles to the protected roles
    chosen = random.choices(roles, k=2)
    lowest_protected = 2000000000
    for r in chosen:
        DBManager.add_guild_protected_colour_role(guild.id, r.id)
        if r.position < lowest_protected:
            lowest_protected = r.position
    if lowest_protected == 2000000000 or lowest_protected == 1:
        expected = 1
    else:
        expected = lowest_protected - 1
    assert role_colour_cog.calculate_custom_colour_role_position(guild) == expected


@pytest.mark.asyncio
async def test_create_custom_colour_role():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    colour: discord.Colour = discord.Colour.from_rgb(16, 16, 16)
    colour_str = "101010"
    with mock.patch('cogs.ColourRole.ColourRole.calculate_custom_colour_role_position', return_value=2) as mock_calc:
        role = await role_colour_cog.create_custom_colour_role(colour, colour_str, ctx)
        assert role in guild.roles
        assert re.match("^KoalaBot\[0x([A-F0-9]{6})\]", role.name), role.name
        assert role.colour.value == colour.value
        assert role.position == 2
        mock_calc.assert_called_once_with(guild)


@pytest.mark.parametrize("num_roles", [0, 1, 2, 5])
@pytest.mark.asyncio
async def test_get_guild_protected_colours(num_roles):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    roles = await make_list_of_custom_colour_roles(guild, num_roles)
    colours = [role.colour for role in roles]
    with mock.patch('cogs.ColourRole.ColourRole.get_protected_roles', return_value=roles) as mock_roles:
        with mock.patch('cogs.ColourRole.ColourRole.get_protected_colours', return_value=colours) as mock_colours:
            result = role_colour_cog.get_guild_protected_colours(ctx)
            mock_roles.assert_called_once_with(guild)
            mock_colours.assert_called_once_with(roles)
            assert result == colours


@pytest.mark.parametrize("num_total, num_protected", [(0, 0), (1, 0), (2, 0), (1, 1), (2, 1), (5, 0), (5, 1), (5, 2)])
@pytest.mark.asyncio
async def test_list_protected_roles(num_total, num_protected):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    roles = await make_list_of_roles(guild, num_total)
    expected = "Roles whose colour is protected are:\r"
    if num_total == 0 or num_protected == 0:
        protected = []
        expected = expected[:-1]
    elif num_protected == num_total:
        protected = roles.copy()
    else:
        protected = random.sample(set(roles), 2)
    for r in protected:
        DBManager.add_guild_protected_colour_role(guild.id, r.id)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "list_protected_role_colours")
    msg: discord.Message = await dpytest.sent_queue.get()
    assert expected in msg.content
    for r in protected:
        assert r.mention in msg.content, r.mention + " " + msg.content


@pytest.mark.parametrize("num_total, num_protected", [(0, 0), (1, 0), (2, 0), (1, 1), (2, 1), (5, 0), (5, 1), (5, 2)])
@pytest.mark.asyncio
async def test_list_custom_colour_allowed_roles(num_total, num_protected):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    roles = await make_list_of_roles(guild, num_total)
    expected = "Roles allowed to have a custom colour are:\r"
    if num_total == 0 or num_protected == 0:
        allowed = []
        expected = expected[:-1]
    elif num_protected == num_total:
        allowed = roles.copy()
    else:
        allowed = random.sample(set(roles), 2)
    for r in allowed:
        DBManager.add_colour_change_role_perms(guild.id, r.id)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "list_custom_colour_allowed_roles")
    msg: discord.Message = await dpytest.sent_queue.get()
    assert expected in msg.content
    for r in allowed:
        assert r.mention in msg.content, r.mention + " " + msg.content


@pytest.mark.asyncio
async def test_on_guild_role_delete():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "store_ctx")
    ctx: commands.Context = utils_cog.get_last_ctx()
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role_list = await make_list_of_roles(guild, 2)
    await role_list[0].delete()
    assert role_list[0] not in guild.roles
    role_list = await make_list_of_roles(guild, 2)
    await role_colour_cog.add_protected_role_colour(ctx, role_str=str(role_list[0].id))
    protected = role_colour_cog.get_protected_roles(guild)
    assert role_list[0] in protected
    await role_list[0].delete()
    protected = role_colour_cog.get_protected_roles(guild)
    assert role_list[0] not in protected
    role_list = await make_list_of_roles(guild, 2)
    await role_colour_cog.add_custom_colour_allowed_role(ctx, role_str=str(role_list[0].id))
    custom_colour_allowed = role_colour_cog.get_custom_colour_allowed_roles(ctx)
    assert role_list[0] in custom_colour_allowed
    await role_list[0].delete()
    custom_colour_allowed = role_colour_cog.get_custom_colour_allowed_roles(ctx)
    assert role_list[0] not in custom_colour_allowed


@pytest.mark.parametrize("num_total, num_protected, test_colour",
                         [(0, 0, random_colour()), (1, 0, random_colour()), (2, 0, random_colour()),
                          (5, 0, random_colour()), (1, 1, random_colour()), (2, 1, random_colour()),
                          (5, 1, random_colour()), (2, 2, random_colour()), (5, 2, random_colour())])
@pytest.mark.asyncio
async def test_is_valid_custom_colour(num_total, num_protected, test_colour):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    await make_list_of_roles(guild, num_total - num_protected)
    protected_roles = await make_list_of_protected_colour_roles(guild, num_protected)
    protected_colours = [role.colour for role in protected_roles]
    lowest_colour_dist = 1000
    for colour in protected_colours:
        d = role_colour_cog.get_rgb_colour_distance(colour, test_colour)
        if d < lowest_colour_dist:
            lowest_colour_dist = d
    assert role_colour_cog.is_valid_custom_colour(test_colour, protected_colours)[0] != (lowest_colour_dist < 30)


@pytest.mark.parametrize("num_members", [0, 1, 2, 5])
@pytest.mark.asyncio
async def test_prune_member_old_colour_roles(num_members):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    colour_role = (await make_list_of_custom_colour_roles(guild, 1))[0]
    test_members = []
    for i in range(num_members):
        member: discord.Member = await dpytest.member_join(name=f"TestMemberWithRole{i}", discrim=i + 1)
        await member.add_roles(colour_role)
        test_members.append(member)
    val = await role_colour_cog.prune_members_old_colour_roles(dpytest.get_config().members)
    assert val
    for member in dpytest.get_config().members:
        assert colour_role not in member.roles


@pytest.mark.asyncio
async def test_add_protected_role_colour():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role = await make_list_of_roles(guild, 1)
    assert independent_get_protected_colours(guild.id) == []
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "add_protected_role_colour " + str(role[0].id))
    assert independent_get_protected_colours(guild.id) == [role[0].id]


@pytest.mark.asyncio
async def test_add_custom_colour_allowed_role():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role = await make_list_of_roles(guild, 1)
    assert independent_get_colour_change_roles(guild.id) == []
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "add_custom_colour_allowed_role " + str(role[0].id))
    assert independent_get_colour_change_roles(guild.id) == [role[0].id]


@pytest.mark.asyncio
async def test_remove_protected_role_colour():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role = (await make_list_of_roles(guild, 1))[0]
    assert independent_get_protected_colours(guild.id) == []
    DBManager.add_guild_protected_colour_role(guild.id, role.id)
    assert independent_get_protected_colours(guild.id) == [role.id]
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "remove_protected_role_colour " + str(role.id))
    assert independent_get_protected_colours(guild.id) == []


@pytest.mark.asyncio
async def test_remove_custom_colour_allowed_role():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role = (await make_list_of_roles(guild, 1))[0]
    assert independent_get_colour_change_roles(guild.id) == []
    DBManager.add_colour_change_role_perms(guild.id, role.id)
    assert independent_get_colour_change_roles(guild.id) == [role.id]
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "remove_custom_colour_allowed_role " + str(role.id))
    assert independent_get_colour_change_roles(guild.id) == []


@pytest.mark.asyncio
async def test_custom_colour_check_failure():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role = (await make_list_of_roles(guild, 1))[0]
    DBManager.add_colour_change_role_perms(guild.id, role.id)
    with pytest.raises(commands.CheckFailure):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "custom_colour ab1234")
        await dpytest.verify_message("You don't have the required role to use this command.")
        await dpytest.verify_message(assert_nothing=True)
    with pytest.raises(commands.CheckFailure):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "custom_colour no")
        await dpytest.verify_message("You don't have the required role to use this command.")
        await dpytest.verify_message(assert_nothing=True)


@pytest.mark.asyncio
async def test_custom_colour_no_allowed_role():
    with pytest.raises(commands.CheckFailure):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "custom_colour ab1234")
        assert "KoalaBot[0xAB1234]" not in [role.name for role in dpytest.get_config().guilds[0].roles]
        assert "KoalaBot[0xAB1234]" not in [role.name for role in dpytest.get_config().members[0].roles]
        await dpytest.verify_message("You don't have the required role to use this command.")
        await dpytest.verify_message(assert_nothing=True)
    with pytest.raises(commands.CheckFailure):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "custom_colour no")
        assert "KoalaBot[0xAB1234]" not in [role.name for role in dpytest.get_config().guilds[0].roles]
        dpytest.verify_message("You don't have the required role to use this command.")
        dpytest.verify_message(assert_nothing=True)


@pytest.mark.asyncio
async def test_custom_colour_no_no_colour_role():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role = (await make_list_of_roles(guild, 1))[0]
    DBManager.add_colour_change_role_perms(guild.id, role.id)
    member: discord.Member = dpytest.get_config().members[0]
    await member.add_roles(role)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "custom_colour no", member=0)
    dpytest.verify_message("Okay, removing your old custom colour role then, if you have one.")
    dpytest.verify_message(f"{member.mention} you don't have any colour roles to remove.")
    dpytest.verify_message(assert_nothing=True)


@pytest.mark.asyncio
async def test_custom_colour_colour_is_protected():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role = (await make_list_of_roles(guild, 1))[0]
    DBManager.add_colour_change_role_perms(guild.id, role.id)
    member: discord.Member = dpytest.get_config().members[0]
    await member.add_roles(role)
    fail_colour = discord.Colour.from_rgb(255, 255, 255)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "custom_colour FEFEFE", member=0)
    dpytest.verify_message(
        f"Colour chosen was too close to an already protected colour {hex(fail_colour.value)}. Please choose a different colour.")
    assert "KoalaBot[0xFEFEFE]" not in [role.name for role in guild.roles]


@pytest.mark.asyncio
async def test_custom_colour_invalid_colour_str():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role = (await make_list_of_roles(guild, 1))[0]
    DBManager.add_colour_change_role_perms(guild.id, role.id)
    member: discord.Member = dpytest.get_config().members[0]
    await member.add_roles(role)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "custom_colour s34a21", member=0)
    dpytest.verify_message(
        f"Invalid colour string specified, make sure it's a valid colour hex.")
    assert len(member.roles) == 2


@pytest.mark.asyncio
async def test_custom_colour_valid():
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role = (await make_list_of_roles(guild, 1))[0]
    DBManager.add_colour_change_role_perms(guild.id, role.id)
    member: discord.Member = dpytest.get_config().members[0]
    await member.add_roles(role)
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "custom_colour e34a21", member=0)
    colour_role = discord.utils.get(guild.roles, name=f"KoalaBot[0xE34A21]")
    dpytest.verify_message(
        f"Your new custom role colour is #E34A21, with the role {colour_role.mention}")
    assert "KoalaBot[0xE34A21]" in [role.name for role in guild.roles]
    assert "KoalaBot[0xE34A21]" in [role.name for role in member.roles]


@pytest.fixture(scope='session', autouse=True)
def setup_db():
    DBManager.get_parent_database_manager().clear_all_tables(DBManager.get_parent_database_manager().fetch_all_tables())
    yield DBManager


@pytest.fixture(scope='function', autouse=True)
async def setup_clean_messages():
    await dpytest.empty_queue()
    yield dpytest
