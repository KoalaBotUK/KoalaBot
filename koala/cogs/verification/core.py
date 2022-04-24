import discord
from discord.ext.commands import Bot
from sqlalchemy import select

from koala.cogs.verification import db, errors
from koala.cogs.verification.log import logger
from koala.cogs.verification.models import VerifiedEmails, ToReVerify, VerifyBlacklist
from koala.db import assign_session


@assign_session
def blacklist_member(user_id, guild_id, role_id, suffix, bot: Bot, **kwargs):
    guild: discord.Guild = bot.get_guild(guild_id)
    role = guild.get_role(role_id)

    if not role:
        raise errors.InvalidArgumentError("Please mention a role in this guild")

    db.add_to_blacklist(user_id, role.id, suffix, **kwargs)


@assign_session
def remove_blacklist_member(user_id, guild_id, role_id, suffix, bot: Bot, **kwargs):
    guild: discord.Guild = bot.get_guild(guild_id)
    role = guild.get_role(role_id)

    if not role:
        raise errors.InvalidArgumentError("Please mention a role in this guild")

    db.remove_from_blacklist(user_id, role.id, suffix, **kwargs)


@assign_session
async def assign_role_to_guild(guild, role, suffix, session):
    results = session.execute(select(VerifiedEmails.u_id).where(VerifiedEmails.email.endswith(suffix),
                                                                VerifiedEmails.u_id.in_(
                                                                    [member.id for member in guild.members]
                                                                ))).scalars().all()
    for verified_email in results:
        try:
            should_re_verify = session.execute(select(ToReVerify)
                                               .filter_by(r_id=role.id, u_id=verified_email.u_id)).all()

            blacklisted = session.execute(select(VerifyBlacklist)
                                          .filter_by(user_id=verified_email.u_id, role_id=role.id, email=suffix)).all()
            if blacklisted or should_re_verify:
                continue

            member = await guild.get_member(verified_email.u_id)
            await member.add_roles(role)
        except AttributeError as e:
            # bot not in guild
            logger.error(exc_info=e)
        except discord.errors.NotFound as e:
            logger.error(f"user with id {verified_email.u_id} not found in {guild}", exc_info=e)
        except discord.errors.Forbidden:
            raise errors.VerifyError(f"I do not have permission to assign {role}. "
                                     f"Make sure I have permission to give roles and {role} is lower than the "
                                     f"KoalaBot role in the hierarchy, then try again.")
