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
    )
    async def subscribe(
        self,
        interaction: discord.Interaction,
        timer: str,
        target_channel: Optional[discord.TextChannel] = None,
    ):
        # Check permissions
        if not await self._check_permissions(interaction):
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
        if not await self._check_permissions(interaction):
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

    async def _check_permissions(self, interaction: discord.Interaction) -> bool:
        member = interaction.guild.get_member(interaction.user.id)

        # Bot owner bypasses permission checks
        if self.bot.is_owner(interaction.user):
            return True

        # Check if user has manage_messages permission
        if not member.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "❌ You need the `Manage Messages` permission to use this command.",
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


async def setup(bot):
    await bot.add_cog(SubscriptionCommands(bot))
