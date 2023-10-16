import pytest

import discord.ext.test as dpytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from koala.cogs.verification import core
from koala.cogs.verification.models import ToReVerify, VerifiedEmails, NonVerifiedEmails, Roles, VerifyBlacklist


@pytest.mark.asyncio
async def test_confirm_reverify(bot, session: Session):
    await dpytest.get_config().guilds[0].create_role(name="emailRole")

    guild = dpytest.get_config().guilds[0]
    user_id = guild.members[0].id
    role_id = guild.roles[1].id
    email_suffix = "@gmail.com"
    email = "testemail"+email_suffix
    token = "12345"

    session.add(ToReVerify(u_id=user_id, r_id=role_id))
    session.add(VerifiedEmails(u_id=user_id, email=email))
    session.add(NonVerifiedEmails(u_id=user_id, email=email, token=token))
    session.add(Roles(s_id=guild.id, r_id=role_id, email_suffix=email_suffix))

    await core.email_verify_confirm(user_id, token, bot, session=session)

    assert session.execute(select(ToReVerify)).all() == []
    assert session.execute(select(NonVerifiedEmails)).all() == []
    assert len(session.execute(select(VerifiedEmails)).all()) == 1


def test_grouped_list_blacklist(bot, session):
    guild = dpytest.get_config().guilds[0]
    user = guild.members[0]
    role = guild.roles[0]

    session.add(VerifyBlacklist(user_id=user.id, role_id=role.id, email_suffix="@test.com"))

    blacklist_map = core.grouped_list_blacklist(guild.id, bot, session=session)

    assert blacklist_map == {user.name: [role.mention+" / @test.com"]}


def test_grouped_list_blacklist_multiple(bot, session):
    guild = dpytest.get_config().guilds[0]
    user = guild.members[0]
    role = guild.roles[0]

    session.add(VerifyBlacklist(user_id=user.id, role_id=role.id, email_suffix="@test.com"))
    session.add(VerifyBlacklist(user_id=user.id, role_id=role.id, email_suffix="@test2.com"))

    blacklist_map = core.grouped_list_blacklist(guild.id, bot, session=session)

    assert blacklist_map == {user.name: [role.mention+" / @test.com", role.mention+" / @test2.com"]}

