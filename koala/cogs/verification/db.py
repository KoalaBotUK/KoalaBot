import discord
import sqlalchemy.orm
from sqlalchemy import select, delete, and_, text

from koala.db import assign_session
from .models import Roles, VerifiedEmails, ToReVerify

@assign_session
def get_potential_emails(member: discord.Member, session: sqlalchemy.orm.Session):
    query = select(Roles.r_id, Roles.email_suffix).filter_by(s_id=member.guild.id)

    # returns sqlalchemy.engine.row.Row
    return session.execute(query).all()

@assign_session
def member_join_email_results(member: discord.Member, suffix, session: sqlalchemy.orm.Session):    
    query = select(VerifiedEmails).where(
                    and_(
                        VerifiedEmails.email.endswith(suffix),
                        VerifiedEmails.u_id == member.id
                    ))
    
    # returns sqlalchemy.engine.row.Row
    return session.execute(query).all()

@assign_session
def member_join_blacklisted(member, role_id, session: sqlalchemy.orm.Session):
    query = select(ToReVerify).filter_by(r_id=role_id, u_id=member.id)

    return session.execute(query).all()