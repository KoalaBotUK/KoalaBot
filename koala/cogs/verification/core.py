#!/usr/bin/env python
import random
import string
from typing import List, Dict

# Futures
# Built-in/Generic Imports
# Libs
import discord
from discord.ext.commands import Bot
from sqlalchemy import select, text, delete, and_
from sqlalchemy.orm import Session

import koalabot
# Own modules
from koala.cogs.verification import db, errors
from koala.cogs.verification.dto import VerifyConfig, VerifyRole
from koala.cogs.verification.errors import VerifyException
from koala.cogs.verification.log import logger
from koala.cogs.verification.models import VerifiedEmails, ToReVerify, VerifyBlacklist, Roles, NonVerifiedEmails
from koala.cogs.verification.utils import send_email
from koala.db import assign_session
# Constants
# Variables
from koala.errors import InvalidArgumentError

'''
COMMANDS
'''


@assign_session
async def set_verify_role(guild_id, roles: List[VerifyRole], bot, **kwargs):
    add_roles: List[VerifyRole] = []
    remove_roles: List[VerifyRole] = [VerifyRole.from_db_roles(r) for r in list_verify_role(guild_id, **kwargs)]
    for role in roles:
        if role in remove_roles:
            remove_roles.remove(role)
        else:
            add_roles.append(role)

    for role in add_roles:
        await add_verify_role(guild_id, role.email_suffix, role.role_id, bot, **kwargs)

    for role in remove_roles:
        remove_verify_role(guild_id, role.email_suffix, role.role_id, **kwargs)

    return get_verify_config_dto(guild_id)


@assign_session
async def add_verify_role(guild_id, email_suffix, role_id, bot: koalabot.KoalaBot, *, session: Session):
    email_suffix = email_suffix.lower()
    guild = bot.get_guild(guild_id)

    role = guild.get_role(role_id)
    if not role:
        raise InvalidArgumentError("Please mention a role in this guild")

    exists = session.execute(select(Roles)
                             .filter_by(s_id=guild_id, r_id=role_id, email_suffix=email_suffix)).all()
    if exists:
        raise VerifyException("Verification is already enabled for that role")

    session.add(Roles(s_id=guild_id, r_id=role_id, email_suffix=email_suffix))
    session.commit()

    await assign_role_to_guild(guild, role, email_suffix)


@assign_session
def remove_verify_role(guild_id, email_suffix, role_id, *, session: Session):
    email_suffix = email_suffix.lower()
    session.execute(delete(Roles).filter_by(s_id=guild_id, r_id=role_id, email_suffix=email_suffix))
    session.commit()


@assign_session
def get_verify_config_dto(guild_id, **kwargs) -> VerifyConfig:
    return VerifyConfig(guild_id, [VerifyRole(r.email_suffix, r.r_id) for r in list_verify_role(guild_id, **kwargs)])


@assign_session
def list_verify_role(guild_id, *, session: Session) -> List[Roles]:
    return session.execute(select(Roles).filter_by(s_id=guild_id)).scalars().all()


@assign_session
def grouped_list_verify_role(guild_id, bot: koalabot.KoalaBot, *, session: Session) -> Dict[str, List[str]]:
    guild = bot.get_guild(guild_id)
    roles = list_verify_role(guild_id, session=session)
    role_dict = {}
    for role in roles:
        d_role = guild.get_role(role.r_id)
        if d_role is None:
            session.execute(delete(Roles).filter_by(r_id=role.r_id))
        elif role.email_suffix in role_dict:
            role_dict[role.email_suffix].append("@" + d_role.name)
        else:
            role_dict[role.email_suffix] = ["@" + d_role.name]
    session.commit()
    return role_dict


@assign_session
async def re_verify_role(guild_id, role_id, bot: koalabot.KoalaBot, *, session: Session):
    exists = session.execute(select(Roles).filter_by(s_id=guild_id, r_id=role_id)).all()

    if not exists:
        raise VerifyException("Verification is not enabled for that role")
    existing_reverify = session.execute(select(ToReVerify.u_id).filter_by(r_id=role_id)).scalars().all()
    guild = bot.get_guild(guild_id)
    role = guild.get_role(role_id)
    for member in role.members:
        await member.remove_roles(role)
        if member.id not in existing_reverify:
            session.add(ToReVerify(u_id=member.id, r_id=role_id))

    session.commit()


@assign_session
async def blacklist_member(user_id, guild_id, role_id, suffix, bot: Bot, **kwargs):
    guild: discord.Guild = bot.get_guild(guild_id)
    role = guild.get_role(role_id)

    if not role:
        raise InvalidArgumentError("Please mention a role in this guild")

    db.add_to_blacklist(user_id, role.id, suffix, **kwargs)
    await remove_roles_for_user(user_id, suffix, bot, **kwargs)


@assign_session
async def remove_blacklist_member(user_id, guild_id, role_id, suffix, bot: Bot, **kwargs):
    guild: discord.Guild = bot.get_guild(guild_id)
    role = guild.get_role(role_id)

    if not role:
        raise InvalidArgumentError("Please mention a role in this guild")

    db.remove_from_blacklist(user_id, role.id, suffix, **kwargs)
    await assign_roles_for_user(user_id, suffix, bot, **kwargs)
    await assign_role_to_guild(guild, role, suffix)


@assign_session
async def email_verify_send(user_id, email, bot, force=False, *, session: Session):
    email = email.lower()
    already_verified = session.execute(select(VerifiedEmails).filter_by(email=email)).scalar()

    to_reverify = session.execute(select(ToReVerify).filter_by(u_id=user_id)).all()

    if already_verified and not to_reverify:
        if force:
            session.delete(already_verified)
            session.commit()
            await remove_roles_for_user(already_verified.u_id, email, bot, session=session)
        elif already_verified.u_id == user_id:
            raise errors.VerifyExistsException("This email is already assigned to your account.")
        else:
            raise errors.VerifyExistsException("This email is already assigned to a different account.")

    verification_code = ''.join(random.choice(string.ascii_letters) for _ in range(8))
    session.add(NonVerifiedEmails(u_id=user_id, email=email, token=verification_code))
    session.commit()

    send_email(email, verification_code)


@assign_session
async def email_verify_remove(user_id, email, bot, *, session: Session):
    entry = session.execute(select(VerifiedEmails).filter_by(u_id=user_id, email=email)).all()

    if not entry:
        raise VerifyException("You have not verified that email")

    session.execute(delete(VerifiedEmails).filter_by(u_id=user_id, email=email))
    session.commit()

    await remove_roles_for_user(user_id, email, bot, session=session)


@assign_session
async def email_verify_confirm(user_id, token, bot, *, session: Session):
    entry = session.execute(select(NonVerifiedEmails).filter_by(token=token, u_id=user_id)).scalar()

    if not entry:
        raise InvalidArgumentError("That is not a valid token")

    session.add(VerifiedEmails(u_id=user_id, email=entry.email))

    session.execute(delete(NonVerifiedEmails).filter_by(token=token, u_id=user_id))

    potential_roles = session.execute(select(Roles.r_id)
                                      .where(text(":email like ('%' || email_suffix)")),
                                      {"email": entry.email}).all()
    if potential_roles:
        for role_id in potential_roles:
            session.execute(delete(ToReVerify).filter_by(r_id=role_id[0], u_id=user_id))

    session.commit()
    await assign_roles_for_user(user_id, entry.email, bot, session=session)


@assign_session
def email_verify_list(user_id, *, session: Session):
    return session.execute(select(VerifiedEmails.email).filter_by(u_id=user_id)).scalars().all()


'''
EVENTS
'''


@assign_session
async def assign_roles_on_startup(bot: koalabot.KoalaBot, *, session: Session):
    results = session.execute(select(Roles.s_id, Roles.r_id, Roles.email_suffix)).all()
    for g_id, r_id, suffix in results:
        guild = bot.get_guild(g_id)
        if not guild:
            logger.error("Verify bot not in guild %s", guild.id)
            continue

        role = guild.get_role(r_id)
        try:
            await assign_role_to_guild(guild, role, suffix)
        except VerifyException as e:
            logger.error(f"Guild {g_id} has not given Koala sufficient permissions to give roles",
                         exc_info=e)


@assign_session
async def send_verify_intro_message(member: discord.Member, *, session: Session):
    guild = member.guild

    potential_emails = session.execute(select(Roles.r_id, Roles.email_suffix)
                                       .filter_by(s_id=guild.id)).all()

    if potential_emails:
        roles = {}
        for role_id, suffix in potential_emails:
            role = guild.get_role(role_id)
            roles[suffix] = role
            results = session.execute(select(VerifiedEmails).where(
                and_(
                    VerifiedEmails.email.endswith(suffix),
                    VerifiedEmails.u_id == member.id
                ))).all()

            blacklisted = session.execute(select(ToReVerify)
                                          .filter_by(r_id=role_id, u_id=member.id)).all()

            if results and not blacklisted:
                await member.add_roles(role)
        message_string = f"""Welcome to {guild.name}. This guild has verification enabled.
Please verify one of the following emails to get the appropriate role using \
`{koalabot.COMMAND_PREFIX}verify your_email@example.com`.
This email is stored so you don't need to verify it multiple times across servers."""
        await member.send(
            content=message_string + "\n" + "\n".join([f"`{x}` for `@{y}`" for x, y in roles.items()]))


'''
UTILS
'''


@assign_session
async def assign_role_to_guild(guild, role, suffix, session):
    results = session.execute(select(VerifiedEmails.u_id).where(VerifiedEmails.email.endswith(suffix),
                                                                VerifiedEmails.u_id.in_(
                                                                    [member.id for member in guild.members]
                                                                ))).scalars().all()
    for user_id in results:
        try:
            should_re_verify = session.execute(select(ToReVerify)
                                               .filter_by(r_id=role.id, u_id=user_id)).all()

            blacklisted = session.execute(select(VerifyBlacklist)
                                          .filter_by(user_id=user_id, role_id=role.id, email_suffix=suffix)).all()
            if blacklisted or should_re_verify:
                continue

            member = guild.get_member(user_id)
            await member.add_roles(role)
        except AttributeError as e:
            # bot not in guild
            logger.error(exc_info=e)
        except discord.errors.NotFound as e:
            logger.error(f"user with id {user_id} not found in {guild}", exc_info=e)
        except discord.errors.Forbidden:
            raise errors.VerifyException(f"I do not have permission to assign {role}. "
                                         f"Make sure I have permission to give roles and {role} is lower than the "
                                         "KoalaBot role in the hierarchy, then try again.")


@assign_session
async def assign_roles_for_user(user_id, email, bot, *, session):
    results = session.execute(select(Roles.s_id, Roles.r_id, Roles.email_suffix)
                              .where(text(":email like ('%' || email_suffix)")), {"email": email}).all()

    for g_id, r_id, suffix in results:
        should_re_verify = session.execute(select(ToReVerify).filter_by(r_id=r_id, u_id=user_id)).all()

        blacklisted = session.execute(select(VerifyBlacklist).filter_by(user_id=user_id, role_id=r_id)
                                      .where(text(":email like ('%' || email_suffix)")), {"email": email}).all()

        if blacklisted or should_re_verify:
            continue
        try:
            guild = bot.get_guild(g_id)
            role = discord.utils.get(guild.roles, id=r_id)
            member = guild.get_member(user_id)
            if not member:
                member = await guild.fetch_member(user_id)
            if not member:
                raise discord.errors.NotFound
            await member.add_roles(role)
        except AttributeError as e:
            # bot not in guild
            logger.error(e)
        except discord.errors.NotFound:
            logger.error(f"user with id {user_id} not found")
        except discord.errors.Forbidden:
            raise errors.VerifyException(
                "I do not have permission to assign a role. Make sure I have permission to give roles and "
                "that is lower than the KoalaBot role in the hierarchy, then try again.")


@assign_session
async def remove_roles_for_user(user_id, email, bot, *, session):
    results = session.execute(select(Roles.s_id, Roles.r_id, Roles.email_suffix)
                              .where(text(":email like ('%' || email_suffix)")), {"email": email}).all()

    for g_id, r_id, suffix in results:
        try:
            guild = bot.get_guild(g_id)
            role = discord.utils.get(guild.roles, id=r_id)
            member = guild.get_member(user_id)
            if not member:
                member = await guild.fetch_member(user_id)
            await member.remove_roles(role)
        except AttributeError as e:
            # bot not in guild
            logger.error(e)
        except discord.errors.NotFound:
            logger.error(f"user with id {user_id} not found in {g_id}")
