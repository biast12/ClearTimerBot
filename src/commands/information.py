import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional


class InformationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler_service = bot.scheduler_service
        self.data_service = bot.data_service

    @app_commands.command(
        name="next", description="Check when the next message clear is scheduled"
    )
    @app_commands.describe(
        target_channel="Channel to check (defaults to current channel)"
    )
    async def next_clear(
        self,
        interaction: discord.Interaction,
        target_channel: Optional[discord.TextChannel] = None,
    ):
        # Check blacklist
        if await self._is_blacklisted(interaction):
            return

        channel = target_channel or interaction.channel
        server_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        # Get next run time
        next_run_time = self.scheduler_service.get_next_run_time(server_id, channel_id)

        if not next_run_time:
            await interaction.response.send_message(
                f"❌ {channel.mention} is not subscribed to message deletion.\n"
                f"Use `/sub` to set up automatic clearing.",
                ephemeral=True,
            )
            return

        # Get timer info from data service
        server = await self.data_service.get_server(server_id)
        timer_info = server.get_channel(channel_id) if server else None

        timestamp = int(next_run_time.timestamp())

        embed = discord.Embed(
            title="⏰ Next Clear Scheduled",
            description=f"Message clear information for {channel.mention}",
            color=discord.Color.blue(),
        )

        if timer_info:
            embed.add_field(name="Timer", value=timer_info.timer, inline=True)

        embed.add_field(name="Next Clear", value=f"<t:{timestamp}:f>", inline=True)
        embed.add_field(name="Time Until", value=f"<t:{timestamp}:R>", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="help", description="Display help information about the bot"
    )
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="ClearTimer Bot Help",
            description="Automatically clear messages in Discord channels on a schedule.",
            color=discord.Color.blue(),
        )

        # Basic Commands
        embed.add_field(
            name="📝 Basic Commands",
            value=(
                "`/sub [timer] [channel]` - Subscribe a channel to automatic clearing\n"
                "`/unsub [channel]` - Unsubscribe a channel\n"
                "`/next [channel]` - Check next clear time\n"
                "`/ping` - Check bot latency\n"
                "`/help` - Show this help message"
            ),
            inline=False,
        )

        # Timer Formats
        embed.add_field(
            name="⏱️ Timer Formats",
            value=(
                "**Intervals:** `1d2h3m` (days, hours, minutes)\n"
                "**Daily Schedule:** `15:30 EST` (time + timezone)\n"
                "**Examples:** `24h`, `1d`, `30m`, `09:00 PST`"
            ),
            inline=False,
        )

        # Permissions
        embed.add_field(
            name="🔒 Required Permissions",
            value=(
                "**For You:** Manage Messages\n"
                "**For Bot:** Read Messages, Manage Messages, Read Message History"
            ),
            inline=False,
        )

        # Links
        # Bot invite URL split for readability
        bot_invite_url = (
            "https://discord.com/oauth2/authorize?"
            "client_id=1290353946308775987&permissions=76800&"
            "integration_type=0&scope=bot"
        )

        embed.add_field(
            name="🔗 Links",
            value=(
                "[Support Server](https://discord.com/invite/ERFffj9Qs7) | "
                f"[Add Bot]({bot_invite_url}) | "
                "[GitHub](https://github.com/biast12/ClearTimerBot)"
            ),
            inline=False,
        )

        embed.set_footer(text="ClearTimer Bot")

        await interaction.response.send_message(embed=embed)

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
    await bot.add_cog(InformationCommands(bot))
