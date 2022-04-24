#!/usr/bin/env python

# Futures
# Built-in/Generic Imports
# Libs
import discord
from discord.ext.commands import Bot
from sqlalchemy import select, text

# Own modules
from koala.cogs.verification import db, errors
from koala.cogs.verification.log import logger
from koala.cogs.verification.models import VerifiedEmails, ToReVerify, VerifyBlacklist, Roles
from koala.db import assign_session

# Constants
# Variables
from koala.errors import InvalidArgumentError


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
                                          .filter_by(user_id=user_id, role_id=role.id, email=suffix)).all()
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
async def assign_roles_for_user(user_id, email, bot, session):
    results = session.execute(select(Roles.s_id, Roles.r_id, Roles.email_suffix)
                              .where(text(":email like ('%' || email_suffix)")), {"email": email}).all()

    for g_id, r_id, suffix in results:
        should_re_verify = session.execute(select(ToReVerify).filter_by(r_id=r_id, u_id=user_id)).all()

        blacklisted = session.execute(select(VerifyBlacklist).filter_by(user_id=user_id, role_id=r_id)
                                      .where(text(":email like ('%' || email)")), {"email": email}).all()

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
async def remove_roles_for_user(user_id, email, bot, session):
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
