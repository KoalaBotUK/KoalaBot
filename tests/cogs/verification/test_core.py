import discord
import discord.ext.test as dpytest
import mock
import pytest
from discord.ext import commands
from sqlalchemy import select, delete
from koala.cogs.verification.dto import VerifyConfig, VerifyRole
from koala.cogs.verification.errors import VerifyException
from koala.errors import InvalidArgumentError

import koalabot
from koala.cogs.verification import core
from koala.cogs.verification.models import VerifiedEmails, ToReVerify, NonVerifiedEmails, Roles, VerifyBlacklist

# Constants
TEST_EMAIL = 'verify_test@koalabot.uk'
TEST_EMAIL_DOMAIN = 'koalabot.uk'


@pytest.fixture(autouse=True)
def delete_tables(session):
    session.execute(delete(VerifiedEmails))
    session.execute(delete(ToReVerify))
    session.execute(delete(NonVerifiedEmails))
    session.execute(delete(Roles))
    session.execute(delete(VerifyBlacklist))
    session.commit()


@pytest.mark.asyncio
async def test_set_verify_role(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]

    dpytest.back.make_role("testRole", guild, id_num=555)
    test_role = Roles(s_id=1234, r_id=555, email_suffix=TEST_EMAIL_DOMAIN)

    roles = [VerifyRole(test_role.email_suffix, test_role.r_id)]

    resp = await core.set_verify_role(guild.id, roles, bot)
    assert type(resp) is VerifyConfig
    assert resp.roles == roles and resp.guild_id == guild.id


@pytest.mark.asyncio
async def test_add_verify_role(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)

    await core.add_verify_role(guild.id, TEST_EMAIL_DOMAIN, role.id, bot)

    roles = core.list_verify_role(guild.id)
    assert roles[0].r_id == 555


@pytest.mark.asyncio
async def test_remove_verify_role(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)

    await core.add_verify_role(guild.id, TEST_EMAIL_DOMAIN, role.id, bot)

    core.remove_verify_role(guild.id, TEST_EMAIL_DOMAIN, role.id)

    roles = core.list_verify_role(guild.id)
    assert roles == []


@pytest.mark.asyncio
async def test_list_verify_roles(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    dpytest.back.make_role("testRole", guild, id_num=555)
    dpytest.back.make_role("testRole2", guild, id_num=777)
    test_role = Roles(s_id=1234, r_id=555, email_suffix=TEST_EMAIL_DOMAIN)
    test_role2 = Roles(s_id=1234, r_id=777, email_suffix=TEST_EMAIL_DOMAIN)

    roles = [VerifyRole(test_role.email_suffix, test_role.r_id), VerifyRole(test_role2.email_suffix, test_role2.r_id)]

    await core.set_verify_role(guild.id, roles, bot)

    roles = core.list_verify_role(guild.id)
    assert roles[0].r_id == 555 and roles[1].r_id == 777


@pytest.mark.asyncio
async def test_grouped_list_verify_roles(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    dpytest.back.make_role("testRole", guild, id_num=555)
    dpytest.back.make_role("testRole2", guild, id_num=777)
    test_role = Roles(s_id=1234, r_id=555, email_suffix=TEST_EMAIL_DOMAIN)
    test_role2 = Roles(s_id=1234, r_id=777, email_suffix=TEST_EMAIL_DOMAIN)

    roles = [VerifyRole(test_role.email_suffix, test_role.r_id), VerifyRole(test_role2.email_suffix, test_role2.r_id)]
    await core.set_verify_role(guild.id, roles, bot)

    resp = core.grouped_list_verify_role(guild.id, bot)
    assert resp == {TEST_EMAIL_DOMAIN: ["@testRole", "@testRole2"]}


@pytest.mark.asyncio
async def test_re_verify_role(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    member: discord.Member = guild.members[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    test_role = Roles(s_id=1234, r_id=555, email_suffix=TEST_EMAIL_DOMAIN)

    roles = [VerifyRole(test_role.email_suffix, test_role.r_id)]
    await core.set_verify_role(guild.id, roles, bot)
    await dpytest.add_role(member, role)

    assert len(member.roles) == 2

    await core.re_verify_role(guild.id, test_role.r_id, bot)

    # a member will always have the @everyone role
    assert len(member.roles) == 1


@pytest.mark.asyncio
async def test_re_verify_no_exist(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    dpytest.back.make_role("testRole", guild, id_num=555)
    test_role = Roles(s_id=1234, r_id=555, email_suffix=TEST_EMAIL_DOMAIN)

    with pytest.raises(VerifyException, match="Verification is not enabled for that role"):
        await core.re_verify_role(guild.id, test_role.r_id, bot)


@pytest.mark.asyncio
async def test_re_verify_exists(bot: commands.Bot, session):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    member: discord.Member = guild.members[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    test_role = Roles(s_id=1234, r_id=555, email_suffix=TEST_EMAIL_DOMAIN)

    roles = [VerifyRole(test_role.email_suffix, test_role.r_id)]
    await core.set_verify_role(guild.id, roles, bot)
    await dpytest.add_role(member, role)

    await core.re_verify_role(guild.id, test_role.r_id, bot)

    resp = session.execute(select(ToReVerify).filter_by(r_id=test_role.r_id)).scalars().all()
    assert len(resp) == 1

    await core.re_verify_role(guild.id, test_role.r_id, bot)
    resp = session.execute(select(ToReVerify).filter_by(r_id=test_role.r_id)).scalars().all()
    assert len(resp) == 1


@pytest.mark.asyncio
async def test_blacklist(bot: commands.Bot, session):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    member: discord.Member = guild.members[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    test_role = Roles(s_id=1234, r_id=555, email_suffix=TEST_EMAIL_DOMAIN)

    roles = [VerifyRole(test_role.email_suffix, test_role.r_id)]
    await core.set_verify_role(guild.id, roles, bot)

    await dpytest.add_role(member, role)
    assert len(member.roles) == 2

    await core.blacklist_member(member.id, guild.id, role.id, TEST_EMAIL_DOMAIN, bot)
    assert len(member.roles) == 1

    resp = session.execute(select(VerifyBlacklist).filter_by(user_id=member.id)).scalars().all()
    assert len(resp) == 1


@pytest.mark.asyncio
async def test_blacklist_fake_role(bot: commands.Bot, session):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    member: discord.Member = guild.members[0]

    with pytest.raises(InvalidArgumentError, match="Please mention a role in this guild"):
        await core.blacklist_member(member.id, guild.id, 666, TEST_EMAIL_DOMAIN, bot)

    resp = session.execute(select(VerifyBlacklist).filter_by(user_id=member.id)).scalars().all()
    assert len(resp) == 0


@pytest.mark.asyncio
async def test_blacklist_already_blacked(bot: commands.Bot, session):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    member: discord.Member = guild.members[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    test_role = Roles(s_id=1234, r_id=555, email_suffix=TEST_EMAIL_DOMAIN)

    roles = [VerifyRole(test_role.email_suffix, test_role.r_id)]
    await core.set_verify_role(guild.id, roles, bot)

    await core.blacklist_member(member.id, guild.id, role.id, TEST_EMAIL_DOMAIN, bot)
    
    with pytest.raises(VerifyException, match="This user verification is already blacklisted"):
        await core.blacklist_member(member.id, guild.id, role.id, TEST_EMAIL_DOMAIN, bot)

    resp = session.execute(select(VerifyBlacklist).filter_by(user_id=member.id)).scalars().all()
    assert len(resp) == 1


@pytest.mark.asyncio
async def test_remove_blacklist(bot: commands.Bot, session):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    member: discord.Member = guild.members[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)
    test_role = Roles(s_id=1234, r_id=555, email_suffix=TEST_EMAIL_DOMAIN)

    roles = [VerifyRole(test_role.email_suffix, test_role.r_id)]
    await core.set_verify_role(guild.id, roles, bot)
    await core.blacklist_member(member.id, guild.id, role.id, TEST_EMAIL_DOMAIN, bot)

    await core.remove_blacklist_member(member.id, guild.id, role.id, TEST_EMAIL_DOMAIN, bot)

    resp = session.execute(select(VerifyBlacklist).filter_by(user_id=member.id)).scalars().all()
    assert len(resp) == 0
    assert len(member.roles) == 2


@pytest.mark.asyncio
async def test_blacklist_remove_fake_role(bot: commands.Bot, session):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    member: discord.Member = guild.members[0]

    with pytest.raises(InvalidArgumentError, match="Please mention a role in this guild"):
        await core.remove_blacklist_member(member.id, guild.id, 666, TEST_EMAIL_DOMAIN, bot)

    resp = session.execute(select(VerifyBlacklist).filter_by(user_id=member.id)).scalars().all()
    assert len(resp) == 0


@pytest.mark.asyncio
async def test_no_blacklisted(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    member: discord.Member = guild.members[0]
    role = dpytest.back.make_role("testRole", guild, id_num=555)

    with pytest.raises(VerifyException, match="This user verification blacklist doesn't exist"):
        await core.remove_blacklist_member(member.id, guild.id, role.id, TEST_EMAIL_DOMAIN, bot)


@pytest.mark.asyncio
async def test_email_verify_send(bot: commands.Bot, session):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    member: discord.Member = guild.members[0]

    await core.email_verify_send(member.id, TEST_EMAIL, bot)

    token = session.execute(select(NonVerifiedEmails.token).filter_by(u_id=member.id, email=TEST_EMAIL)).scalar()

    assert token


@pytest.mark.asyncio
async def test_email_verify_send_fake_email(bot: commands.Bot):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    member: discord.Member = guild.members[0]

    with pytest.raises(VerifyException, match="No Valid Emails found"):
        await core.email_verify_send(member.id, "asdfjkl", bot)


@pytest.mark.asyncio
async def test_email_verify_send_duplicate(bot: commands.Bot, session):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    member: discord.Member = guild.members[0]

    session.add(VerifiedEmails(u_id=member.id, email=TEST_EMAIL))
    session.commit()
    
    with pytest.raises(VerifyException, match="This email is already assigned to your account"):
        await core.email_verify_send(member.id, TEST_EMAIL, bot)


@pytest.mark.asyncio
async def test_email_verify_send_another_email(bot: commands.Bot, session):
    guild: discord.Guild = dpytest.get_config().guilds[0]
    member: discord.Member = guild.members[0]

    session.add(VerifiedEmails(u_id=1234567, email=TEST_EMAIL))
    session.commit()
    
    with pytest.raises(VerifyException, match="This email is already assigned to a different account"):
        await core.email_verify_send(member.id, TEST_EMAIL, bot)