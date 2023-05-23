# Built-in/Generic Imports
import time

# Libs
import discord
import parsedatetime.parsedatetime
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session

# Own modules
import koalabot
from koala.db import assign_session
from .db import VoteManager, get_results, create_embed, add_reactions
from .log import logger
from .models import Votes
from .option import Option
from .utils import make_result_embed


vm = VoteManager()
vm.load_from_db()


async def update_vote_message(bot: koalabot.KoalaBot, message_id, user_id):
    """
    Updates the vote message with the currently selected option
    :param message_id: id of the message that was reacted on
    :param user_id: id of the user who reacted
    """
    vote = bot.vote_manager.was_sent_to(message_id)
    user = bot.bot.get_user(user_id)
    if vote and not user.bot:
        msg = await user.fetch_message(message_id)
        embed = msg.embeds[0]
        choice = None
        for reaction in msg.reactions:
            if reaction.count > 1:
                choice = reaction
                break
        if choice:
            embed.set_footer(text=f"You will be voting for {choice.emoji} - {vote.options[VoteManager.emote_reference[choice.emoji]].head}")
        else:
            embed.set_footer(text="There are no valid choices selected")
        await msg.edit(embed=embed)


@assign_session
async def vote_end_loop(bot: koalabot.KoalaBot, session: Session):
    try:
        now = time.time()
        votes = session.execute(select(Votes.vote_id, Votes.author_id, Votes.guild_id, Votes.title, Votes.end_time)
                                .where(Votes.end_time < now)).all()
        for v_id, a_id, g_id, title, end_time in votes:
            if v_id in vm.sent_votes.keys():
                vote = vm.get_vote_from_id(v_id)
                results = await get_results(bot, vote)
                embed = await make_result_embed(vote, results)
                try:
                    if vote.chair:
                        try:
                            chair = await bot.fetch_user(vote.chair)
                            await chair.send(f"Your vote {title} has closed")
                            await chair.send(embed=embed)
                        except discord.Forbidden:
                            user = await bot.fetch_user(vote.author)
                            await user.send(f"Your vote {title} has closed")
                            await user.send(embed=embed)
                    else:
                        try:
                            user = await bot.fetch_user(vote.author)
                            await user.send(f"Your vote {title} has closed")
                            await user.send(embed=embed)
                        except discord.Forbidden:
                            guild = await bot.fetch_guild(vote.guild)
                            user = await bot.fetch_user(guild.owner_id)
                            await user.send(f"A vote in your guild titled {title} has closed and the chair is unavailable.")
                            await user.send(embed=embed)
                    session.execute(delete(Votes).filter_by(vote_id=vote.id))
                    session.commit()
                    vm.cancel_sent_vote(vote.id)
                except Exception as e:
                    session.execute(update(Votes).filter_by(vote_id=vote.id).values(end_time=time.time() + 86400))
                    session.commit()
                    logger.error(f"error in vote loop: {e}")
    except Exception as e:
        logger.error("Exception in outer vote loop: %s" % e, exc_info=e)


@assign_session
def start_vote(bot: koalabot.KoalaBot, title, author_id, guild_id, session: Session):
    guild_name = bot.get_guild(guild_id)
    
    if vm.has_active_vote(author_id):
        return f"You already have an active vote in {guild_name}. Please send that with `{koalabot.COMMAND_PREFIX}vote send` before creating a new one."

    in_db = session.execute(select(Votes).filter_by(title=title, author_id=author_id)).all()
    if in_db:
        return f"You already have a vote with title {title} sent!"

    if len(title) > 200:
        return "Title too long"

    vm.create_vote(author_id, guild_id, title)
    return f"Vote titled `{title}` created for guild {guild_name}. Use `{koalabot.COMMAND_PREFIX}help vote` to see how to configure it."


def set_roles(bot: koalabot.KoalaBot, author_id, guild_id, role_id, action):
    vote = vm.get_configuring_vote(author_id)
    role = bot.get_guild(guild_id).get_role(role_id)

    if action == "add":
        vote.add_role(role_id)
        return f"Vote will be sent to those with the {role.name} role"

    if action == "remove":
        vote.remove_role(role_id)
        return f"Vote will no longer be sent to those with the {role.name} role"
    

async def set_chair(bot: koalabot.KoalaBot, author_id, chair_id=None):
    vote = vm.get_configuring_vote(author_id)

    if chair_id:
        chair = bot.get_user(chair_id)
        try:
            await chair.send(f"You have been selected as the chair for vote titled {vote.title}")
            vote.set_chair(chair.id)
            return f"Set chair to {chair.name}"
        except discord.Forbidden:
            return "Chair not set as requested user is not accepting direct messages."
    else:
        vote.set_chair(None)
        return "Results will be sent to the channel vote is closed in"
    

def set_channel(bot: koalabot.KoalaBot, author_id, channel_id=None):
    vote = vm.get_configuring_vote(author_id)
    channel = bot.get_channel(channel_id)

    if channel:
        vote.set_vc(channel.id)
        return f"Set target channel to {channel.name}"
    else:
        vote.set_vc()
        return "Removed channel restriction on vote"
    

# OPTION ATTRIBUTES TITLE, DESCRPTION (OBJECT!)
# NO MORE +

def add_option(author_id, option):
    vote = vm.get_configuring_vote(author_id)
    
    if len(vote.options) > 9:
        return "Vote has maximum number of options already (10)"
    
    if 'header' not in option or 'body' not in option:
        return "Option should have both header and body."
    
    current_option_length = sum([len(x.head) + len(x.body) for x in vote.options])

    if current_option_length + len(option['header']) + len(option['body']) > 1500:
        return "Option string is too long. The total length of all the vote options cannot be over 1500 characters."
    
    # moved check for '+' in string to cog
    
    vote.add_option(Option(option['header'], option['body'], vm.generate_unique_opt_id()))
    return f"Option {option['header']} with description {option['body']} added to vote"


def remove_option(author_id, index):
    vote = vm.get_configuring_vote(author_id)
    try:
        vote.remove_option(index)
        return f"Option number {index} removed"
    except IndexError:
        return f"Option number {index} not found"


def set_end_time(author_id, time_string):
    now = time.time()
    vote = vm.get_configuring_vote(author_id)
    cal = parsedatetime.Calendar()
    end_time_readable = cal.parse(time_string)[0]
    end_time = time.mktime(end_time_readable)
    if (end_time - now) < 0:
        return "You can't set a vote to end in the past"
    # if (end_time - now) < 599:
    #     return "Please set the end time to be at least 10 minutes in the future."
    vote.set_end_time(end_time)
    return f"Vote set to end at {time.strftime('%Y-%m-%d %H:%M:%S', end_time_readable)} UTC"


def preview(author_id):
    vote = vm.get_configuring_vote(author_id)
    return [create_embed(vote), vote]


def cancel_vote(author_id, title):
    v_id = vm.vote_lookup[(author_id, title)]
    if v_id in vm.sent_votes.keys():
        vm.cancel_sent_vote(v_id)
    else:
        vm.cancel_configuring_vote(author_id)
    return f"Vote {title} has been cancelled."


@assign_session
def current_votes(author_id, guild_id, session: Session):
    embed = discord.Embed(title="Your current votes")
    votes = session.execute(select(Votes.title).filter_by(author_id=author_id, guild_id=guild_id)).all()
    body_string = ""
    if len(votes) > 0:
        for title in votes:
            body_string += f"{title[0]}\n"
        embed.add_field(name="Vote Title", value=body_string, inline=False)
    else:
        embed.description = "No current votes"
    return embed


async def send_vote(bot: koalabot.KoalaBot, author_id, guild_id):
    vote = vm.get_configuring_vote(author_id)
    guild = bot.get_guild(guild_id)

    if not vote.is_ready():
        return "Please add more than 1 option to vote for"

    vm.configuring_votes.pop(author_id)
    vm.sent_votes[vote.id] = vote

    users = [x for x in guild.members if not x.bot]
    if vote.target_voice_channel:
        vc_users = discord.utils.get(guild.voice_channels, id=vote.target_voice_channel).members
        users = list(set(vc_users) & set(users))
    if vote.target_roles:
        role_users = []
        for role_id in vote.target_roles:
            role = discord.utils.get(guild.roles, id=role_id)
            role_users += role.members
        role_users = list(dict.fromkeys(role_users))
        users = list(set(role_users) & set(users))
    for user in users:
        try:
            msg = await user.send(f"You have been asked to participate in this vote from {guild.name}.\nPlease react to make your choice (You can change your mind until the vote is closed)", embed=create_embed(vote))
            vote.register_sent(user.id, msg.id)
            await add_reactions(vote, msg)
        except discord.Forbidden:
            logger.error(f"tried to send vote to user {user.id} but direct messages are turned off.")
    return f"Sent vote to {len(users)} users"


async def close(bot: koalabot.KoalaBot, author_id, title):
    vote_id = vm.vote_lookup[(author_id, title)]
    if vote_id not in vm.sent_votes.keys():
        if author_id in vm.configuring_votes.keys():
            return f"That vote has not been sent yet. Please send it to your audience with {koalabot.COMMAND_PREFIX}vote send {title}"
        else:
            return "You have no votes of that title to close"

    vote = vm.get_vote_from_id(vote_id)
    results = await get_results(bot, vote)
    vm.cancel_sent_vote(vote.id)
    embed = await make_result_embed(vote, results)
    if vote.chair:
        try:
            chair = await bot.fetch_user(vote.chair)
            await chair.send(embed=embed)
            return f"Sent results to {chair}"
        except discord.Forbidden:
            return ["Chair does not accept direct messages, sending results here.", embed]
    else:
        return embed
    

async def results(bot: koalabot.KoalaBot, author_id, title):
    vote_id = vm.vote_lookup.get((author_id, title))
    # author = bot.get_user(author_id)

    if vote_id is None:
        raise ValueError(f"{title} is not a valid vote title for user with id {author_id}")

    if vote_id not in vm.sent_votes.keys():
        if author_id in vm.configuring_votes.keys():
            return f"That vote has not been sent yet. Please send it to your audience with {koalabot.COMMAND_PREFIX}vote send {title}"
        else:
            return "You have no votes of that title to check"

    vote = vm.get_vote_from_id(vote_id)
    results = await get_results(bot, vote)
    embed = await make_result_embed(vote, results)
    return embed