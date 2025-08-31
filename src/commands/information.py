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

        # Use Components v2 for next clear display
        from src.components.information import NextClearView
        
        view = NextClearView(channel, next_run_time, timer_info)
        await interaction.response.send_message(view=view)

    @app_commands.command(
        name="help", description="Display help information about the bot"
    )
    async def help_command(self, interaction: discord.Interaction):
        # Use Components v2 for help display
        from src.components.information import HelpView
        
        view = HelpView()
        await interaction.response.send_message(view=view)

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
