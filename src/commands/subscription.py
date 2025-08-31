import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from src.utils.timer_parser import TimerParseError
from src.utils.logger import logger, LogArea


class SubscriptionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_service = bot.data_service
        self.scheduler_service = bot.scheduler_service
        self.timer_parser = bot.scheduler_service.timer_parser

    @app_commands.command(
        name="sub", description="Subscribe a channel to automatic message deletion"
    )
    @app_commands.describe(
        timer="Timer format: '24' for hours, '1d12h30m', or '15:30 EST' for daily at specific time",
        target_channel="Channel to clear (defaults to current channel)",
        ignored_message="Message ID or link to ignore during clearing (optional)",
    )
    async def subscribe(
        self,
        interaction: discord.Interaction,
        timer: str,
        target_channel: Optional[discord.TextChannel] = None,
        ignored_message: Optional[str] = None,
    ):
        # Check permissions
        if not await self._check_permissions(interaction, target_channel):
            return

        # Check blacklist
        if await self._is_blacklisted(interaction):
            return

        channel = target_channel or interaction.channel
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Check if already subscribed
        if self.scheduler_service.job_exists(server_id, channel_id):
            await interaction.response.send_message(
                f"❌ {channel.mention} already has a timer set. Use `/unsub` to remove it first.",
                ephemeral=True,
            )
            return

        # Parse timer
        try:
            trigger, next_run_time = self.timer_parser.parse(timer)
        except TimerParseError as e:
            await interaction.response.send_message(
                f"❌ Invalid timer: {e}", ephemeral=True
            )
            return

        # Add to scheduler
        self.scheduler_service.add_job(
            channel_id=channel_id,
            server_id=server_id,
            trigger=trigger,
            channel=channel,
            next_run_time=next_run_time,
        )

        # Save to data service
        server = await self.data_service.get_server(server_id)
        if not server:
            server = await self.data_service.add_server(
                server_id, interaction.guild.name
            )

        server.add_channel(channel_id, timer, next_run_time)
        
        # Add ignored message if provided
        message_id = None
        if ignored_message:
            message_id = self._extract_message_id(ignored_message)
            if message_id:
                server.channels[channel_id].add_ignored_message(message_id)
        
        await self.data_service.save_servers()

        # Send success message
        timestamp = int(next_run_time.timestamp())
        embed = discord.Embed(
            title="✅ Channel Subscribed",
            description=f"Messages in {channel.mention} will be cleared automatically.",
            color=discord.Color.green(),
        )
        embed.add_field(name="Timer", value=timer, inline=True)
        embed.add_field(name="Next Clear", value=f"<t:{timestamp}:f>", inline=True)
        embed.add_field(name="Time Until", value=f"<t:{timestamp}:R>", inline=True)
        
        if message_id:
            embed.add_field(name="Ignored Message", value=f"Message ID: {message_id}", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="ignoremsg",
        description="Toggle a message to be ignored during channel clearing"
    )
    @app_commands.describe(
        message="Message ID or link to toggle ignore status",
        target_channel="Channel with the subscription (defaults to current channel)"
    )
    async def ignore_message(
        self,
        interaction: discord.Interaction,
        message: str,
        target_channel: Optional[discord.TextChannel] = None,
    ):
        # Check permissions
        if not await self._check_permissions(interaction, target_channel):
            return

        # Check blacklist
        if await self._is_blacklisted(interaction):
            return

        channel = target_channel or interaction.channel
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Check if channel is subscribed
        if not self.scheduler_service.job_exists(server_id, channel_id):
            await interaction.response.send_message(
                f"❌ {channel.mention} is not subscribed to message deletion. Use `/sub` first.",
                ephemeral=True,
            )
            return

        # Extract message ID
        message_id = self._extract_message_id(message)
        if not message_id:
            await interaction.response.send_message(
                "❌ Invalid message ID or link format. Please provide a valid message ID or Discord message link.",
                ephemeral=True,
            )
            return

        # Get server and channel data
        server = await self.data_service.get_server(server_id)
        if not server or channel_id not in server.channels:
            await interaction.response.send_message(
                f"❌ Could not find subscription data for {channel.mention}.",
                ephemeral=True,
            )
            return

        channel_timer = server.channels[channel_id]
        
        # Toggle logic - remove if exists, add if doesn't exist
        if message_id in channel_timer.ignored_messages:
            # Remove the message
            channel_timer.remove_ignored_message(message_id)
            await self.data_service.save_servers()
            
            embed = discord.Embed(
                title="✅ Message Removed from Ignore List",
                description=f"Message `{message_id}` will no longer be ignored in {channel.mention}.",
                color=discord.Color.green(),
            )
            embed.add_field(
                name="Action", 
                value="Removed",
                inline=True
            )
            embed.add_field(
                name="Total Ignored Messages", 
                value=len(channel_timer.ignored_messages),
                inline=True
            )
            await interaction.response.send_message(embed=embed)
        else:
            # Add the message
            channel_timer.add_ignored_message(message_id)
            await self.data_service.save_servers()
            
            embed = discord.Embed(
                title="✅ Message Added to Ignore List",
                description=f"Message `{message_id}` will be ignored during clearing in {channel.mention}.",
                color=discord.Color.green(),
            )
            embed.add_field(
                name="Action", 
                value="Added",
                inline=True
            )
            embed.add_field(
                name="Total Ignored Messages", 
                value=len(channel_timer.ignored_messages),
                inline=True
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="unsub",
        description="Unsubscribe a channel from automatic message deletion",
    )
    @app_commands.describe(
        target_channel="Channel to unsubscribe (defaults to current channel)"
    )
    async def unsubscribe(
        self,
        interaction: discord.Interaction,
        target_channel: Optional[discord.TextChannel] = None,
    ):
        # Check permissions
        if not await self._check_permissions(interaction, target_channel):
            return

        # Check blacklist
        if await self._is_blacklisted(interaction):
            return

        channel = target_channel or interaction.channel
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Check if subscribed
        if not self.scheduler_service.job_exists(server_id, channel_id):
            await interaction.response.send_message(
                f"❌ {channel.mention} is not subscribed to message deletion.",
                ephemeral=True,
            )
            return

        # Remove from scheduler
        self.scheduler_service.remove_job(server_id, channel_id)

        # Remove from data service
        server = await self.data_service.get_server(server_id)
        if server:
            server.remove_channel(channel_id)
            await self.data_service.save_servers()

        # Send success message
        embed = discord.Embed(
            title="✅ Channel Unsubscribed",
            description=f"{channel.mention} has been unsubscribed from automatic message deletion.",
            color=discord.Color.green(),
        )

        await interaction.response.send_message(embed=embed)

    async def _check_permissions(self, interaction: discord.Interaction, target_channel: discord.TextChannel = None) -> bool:
        member = interaction.guild.get_member(interaction.user.id)

        # Bot owner bypasses user permission checks
        if not self.bot.is_owner(interaction.user):
            # Check if user has manage_messages permission
            if not member.guild_permissions.manage_messages:
                await interaction.response.send_message(
                    "❌ You need the `Manage Messages` permission to use this command.",
                    ephemeral=True,
                )
                return False

        # Check bot permissions in the target channel
        channel = target_channel or interaction.channel
        bot_permissions = channel.permissions_for(interaction.guild.me)
        
        required_perms = {
            'view_channel': bot_permissions.view_channel,
            'send_messages': bot_permissions.send_messages,
            'read_message_history': bot_permissions.read_message_history,
            'manage_messages': bot_permissions.manage_messages,
            'embed_links': bot_permissions.embed_links,
            'use_application_commands': bot_permissions.use_application_commands
        }
        
        missing_perms = [perm.replace('_', ' ').title() for perm, has_perm in required_perms.items() if not has_perm]
        
        if missing_perms:
            await interaction.response.send_message(
                f"❌ I'm missing the following permissions in {channel.mention}: {', '.join(missing_perms)}",
                ephemeral=True,
            )
            return False

        return True

    async def _is_blacklisted(self, interaction: discord.Interaction) -> bool:
        server_id = str(interaction.guild.id)

        if await self.data_service.is_blacklisted(server_id):
            await interaction.response.send_message(
                "❌ This server has been blacklisted and cannot use this bot.",
                ephemeral=True,
            )
            return True

        return False
    
    def _extract_message_id(self, message_input: str) -> Optional[str]:
        """Extract message ID from either a message link or direct ID"""
        import re
        
        # Check if it's a message link
        link_pattern = r"https://discord(?:app)?\.com/channels/\d+/\d+/(\d+)"
        match = re.match(link_pattern, message_input)
        if match:
            return match.group(1)
        
        # Check if it's a direct message ID (digits only)
        if message_input.isdigit():
            return message_input
        
        return None


async def setup(bot):
    await bot.add_cog(SubscriptionCommands(bot))
