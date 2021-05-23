# Discord-ext-menu is needed, it can be installed via python -m pip install -U git+https://github.com/Rapptz/discord-ext-menus
import discord, KoalaBot, os
from discord.ext import commands, menus
from utils import KoalaDBManager
from collections import OrderedDict, deque, Counter
"""
KoalaBot Info Commands
Contains: userinfo, serverinfo, roleinfo and channelinfo
Author: SnowyJaguar#1034
"""

class Info(commands.Cog):
    def __init__(self, client):
        self.client = client
    """
        Initialises local variables
        :param bot: The bot client for this cog
        """
    def perm_format(self, perm):
        return perm.replace("_", " ").replace("guild", "server").title()

    @commands.command(aliases=["user-info", "userinfo", "memberinfo", "member-info"])
    async def whois(self, ctx, *, member : discord.Member=None):
        guild = ctx.guild
        member = member or ctx.author
        key_perms = ["administrator", "manage_guild", "manage_roles", "manage_channels", "manage_messages", "manage_webhooks", "manage_nicknames", "manage_emojis", "kick_members", "mention_everyone"]
        has_key = [perm for perm in key_perms if getattr(member.guild_permissions, perm)]
        roles = member.roles[1:]
        user = ctx.author
        roles.reverse()

        if not roles:
    
            try: 
                embed = discord.Embed(colour = member.color, timestamp = ctx.message.created_at, description = member.mention)
                embed = discord.Embed(title = f"{member.name}#{member.discriminator}", description = f"Status: **{member.status}**\n*{member.activity.name}*")
                embed.set_author(name = f"{member.id}", icon_url = member.avatar_url)
                embed.set_thumbnail(url = member.avatar_url)
                embed.set_footer(text = f'{user.name}#{member.discriminator} | {user.id}')
                
                embed.add_field(name = "Joined Server:", value = member.joined_at.strftime("%a, %b %w, %Y %I:%M %p"), inline = False)
                embed.add_field(name = "Avatar", value = f"[Link]({member.avatar_url_as(static_format='png')})", inline = True)
                embed.add_field(name = "Joined Discord:", value = member.created_at.strftime("%a, %b %w, %Y %I:%M %p"), inline = True)
                embed.add_field(name = f'Roles: 0', value = "None", inline = False)

                await ctx.send(embed = embed)

            except:
                embed = discord.Embed(colour=member.color, timestamp=ctx.message.created_at, description=member.mention)
                embed = discord.Embed(title = f"{member.name}#{member.discriminator}", description = f"Status: **{member.status}**")
                embed.set_author(name = f"{member.id}", icon_url = member.avatar_url)
                embed.set_thumbnail(url = member.avatar_url)
                embed.set_footer(text = f'{user.name}#{member.discriminator} | {user.id}')

                embed.add_field(name = "Joined Server:", value = member.joined_at.strftime("%a, %b %w, %Y %I:%M %p"), inline = True)
                embed.add_field(name = "Avatar", value = f"[Link]({member.avatar_url_as(static_format='png')})", inline = True)
                embed.add_field(name="Joined Discord:", value = member.created_at.strftime("%a, %b %w, %Y %I:%M %p"), inline = True)
                embed.add_field(name = f'Roles: 0', value = "None", inline = False)
                await ctx.send(embed = embed)
                return
        if not has_key:
            try: 
                embed = discord.Embed(colour = member.color, timestamp = ctx.message.created_at, description = member.mention)
                embed = discord.Embed(title = f"{member.name}#{member.discriminator}", description = f"Status: **{member.status}**\n*{member.activity.name}*")
                embed.set_author(name = f"{member.id}", icon_url = member.avatar_url)
                embed.set_thumbnail(url = member.avatar_url)
                embed.set_footer(text = f'{user.name}#{member.discriminator} | {user.id}')

                embed.add_field(name = "Joined Server:", value = member.joined_at.strftime("%a, %b %w, %Y %I:%M %p"), inline = False)
                embed.add_field(name = "Avatar", value = f"[Link]({member.avatar_url_as(static_format='png')})", inline = True)    
                embed.add_field(name = "Joined Discord:", value = member.created_at.strftime("%a, %b %w, %Y %I:%M %p"), inline = True)
                embed.add_field(name = f'Roles: {len(roles)}', value = " ".join([role.mention for role in roles]), inline = False) 
                await ctx.send(embed = embed)
            
            except:
            
                embed = discord.Embed(colour=member.color, timestamp=ctx.message.created_at, description=member.mention)
                embed = discord.Embed(title = f"{member.name}#{member.discriminator}", description = f"Status: **{member.status}**")
                embed.set_author(name = f"{member.id}", icon_url = member.avatar_url)
                embed.set_thumbnail(url = member.avatar_url)
                embed.set_footer(text = f'{user.name}#{member.discriminator} | {user.id}')
                
                embed.add_field(name = "Joined Server:", value = member.joined_at.strftime("%a, %b %w, %Y %I:%M %p"), inline = True) 
                embed.add_field(name = "Avatar", value = f"[Link]({member.avatar_url_as(static_format='png')})", inline = True)   
                embed.add_field(name = "Joined Discord:", value=member.created_at.strftime("%a, %b %w, %Y %I:%M %p"), inline = True)
                embed.add_field(name = "Avatar", value=f"[Link]({member.avatar_url_as(static_format='png')})")
                embed.add_field(name = f'Roles: {len(roles)}', value = " ".join([role.mention for role in roles]), inline = False)
                await ctx.send(embed = embed)
                return
        if roles:
            try: 
                embed = discord.Embed(colour = member.color, timestamp = ctx.message.created_at, description = member.mention)
                embed = discord.Embed(title = f"{member.name}#{member.discriminator}", description = f"Status: **{member.status}**\n*{member.activity.name}*")
                embed.set_author(name = f"{member.id}", icon_url = member.avatar_url)
                embed.set_thumbnail(url = member.avatar_url)
                embed.set_footer(text = f'{user.name}#{member.discriminator} | {user.id}')

                embed.add_field(name = "Joined Server:", value = member.joined_at.strftime("%a, %b %w, %Y %I:%M %p"), inline = True)
                embed.add_field(name = "Avatar", value = f"[Link]({member.avatar_url_as(static_format='png')})", inline = True)   
                embed.add_field(name = "Joined Discord:", value = member.created_at.strftime("%a, %b %w, %Y %I:%M %p"), inline = True)
                embed.add_field(name = f'Roles: {len(roles)}', value = " ".join([role.mention for role in roles]), inline = False)
                embed.add_field(name = f'Core permissions', value = ", ".join(has_key).replace("_"," ").title(), inline = False)
                await ctx.send(embed = embed)

            except:
                embed = discord.Embed(colour = member.color, timestamp = ctx.message.created_at, description = member.mention)
                embed = discord.Embed(title = f"{member.name}#{member.discriminator}", description = f"Status: **{member.status}**", color = 0x00aa6e)
                embed.set_author(name = f"{member.id}", icon_url = member.avatar_url)
                embed.set_thumbnail(url = member.avatar_url)
                embed.set_footer(text = f'{user.name}#{user.discriminator} | {user.id}')
                
                embed.add_field(name = "Joined Server:", value = member.joined_at.strftime("%a, %b %w, %Y %I:%M %p"), inline = True)
                embed.add_field(name = "Avatar", value = f"[Link]({member.avatar_url_as(static_format='png')})")   
                embed.add_field(name = "Joined Discord:", value = member.created_at.strftime("%a, %b %w, %Y %I:%M %p"), inline = True)
                embed.add_field(name = f'Roles: {len(roles)}', value = " ".join([role.mention for role in roles]), inline = False)
                embed.add_field(name = f'Core permissions', value = ", ".join(has_key).replace("_"," ").title(), inline = False)
                await ctx.send(embed = embed)
                return

    @whois.error
    async def whois_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(description = f"<:error_1:840895769207898112> Couldn't find that user ", color = discord.Color.red())
            await ctx.send(embed = embed)
        else:
            print(error)

    @commands.command(aliases=["guildinfo", "serverstats", "guildstats", "server-info", "guild-info", "server-stats", "guild-stats"])
    async def serverinfo(self, ctx):
        guild = ctx.guild
        emoji_stats = Counter()
        for emoji in guild.emojis:
            if emoji.animated:
                    emoji_stats['animated'] += 1
                    emoji_stats['animated_disabled'] += not emoji.available
            else:
                emoji_stats['regular'] += 1
                emoji_stats['disabled'] += not emoji.available

            fmt = f'Regular: {emoji_stats["regular"]}/{guild.emoji_limit} | Animated: {emoji_stats["animated"]}/{guild.emoji_limit}'\

            if emoji_stats['disabled'] or emoji_stats['animated_disabled']:
                fmt = f'{fmt}Disabled: {emoji_stats["disabled"]} regular, {emoji_stats["animated_disabled"]} animated\n'

            fmt = f'{fmt} | Total Emojis: {len(guild.emojis)}/{guild.emoji_limit*2}'

        embed = discord.Embed(title = f"{guild.name}", description = f"Server created on {guild.created_at.strftime('%a, %b %w, %Y %I:%M %p')}", color = 0x00aa6e)
        embed.set_author(name = f"{guild.id}", icon_url = guild.icon_url)
        embed.set_thumbnail(url = guild.icon_url)
        # Cluster related Information for if/when the bot gets clustered.
        #if ctx.guild:
            #embed.set_footer(text = f"Cluster: {self.cluster} | Shard: {ctx.guild.shard_id + 1}")
        #else:
            #embed.set_footer(text = f"Cluster: {self.cluster} | Shard: {self.shard_count}")
        embed.add_field(name = "Owner", value = f"{guild.owner.name}#{guild.owner.discriminator}" if guild.owner_id else "Unknown")
        embed.add_field(name = "Icon", value = f"[Link]({guild.icon_url_as(static_format='png')})" if guild.icon else "*Not set*")
        embed.add_field(name = "Region", value = guild.region.name.title())
        embed.add_field(name = "\nEmotes", value = fmt, inline = False)
        embed.add_field(name = "Members", value = guild.member_count, inline = True)
        embed.add_field(name = "Channels", value = len(guild.channels), inline = True)
        embed.add_field(name = "Roles", value = len(guild.roles), inline = True)
        embed.add_field(name = "Server Boosts", value = (guild.premium_subscription_count), inline = True)
        embed.add_field(name = "Server Boost Level", value = (guild.premium_tier), inline = True)
        await ctx.send(embed = embed)

    @commands.command(description = "Show a member's permission in a channel when specified.", usage = "permissions <member> [channel]", aliases = ["perms"])
    async def permissions(self, ctx, member: discord.Member = None, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        if member is None:
            member = ctx.author
        permissions = channel.permissions_for(member)
        embed = discord.Embed(title = "Permission Information", colour = 0x00aa6e)
        embed.set_author(name = f"{member.name}#{member.discriminator}", icon_url = member.avatar_url)
        embed.add_field(name = "Allowed", value = ", ".join([self.perm_format(name) for name, value in permissions if value]), inline = False)
        embed.add_field(name = "Denied", value = ", ".join([self.perm_format(name) for name, value in permissions if not value]), inline = False)
        await ctx.send(embed = embed)
            
def setup(bot: KoalaBot) -> None:
    """
    Load this cog to the KoalaBot.
    :param bot: the bot client for KoalaBot
    """
    bot.add_cog(Info(bot))
    print("Info is ready")