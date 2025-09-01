import discord
from discord import app_commands
from discord.ext import commands
import time
from src.utils.command_validation import CommandValidator, ValidationCheck


class UtilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_service = bot.data_service
        self.validator = CommandValidator(bot)

    @app_commands.command(
        name="help", description="Display help information about the bot"
    )
    async def help_command(self, interaction: discord.Interaction):
        # Check if server is blacklisted
        server_id = str(interaction.guild.id)
        if await self.data_service.is_blacklisted(server_id):
            from src.components.utility import BlacklistedServerView
            view = BlacklistedServerView()
            await interaction.response.send_message(view=view, ephemeral=True)
            return
        
        # Help display
        from src.components.utility import HelpView
        
        view = HelpView()
        await interaction.response.send_message(view=view)

    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        # Validate command - blacklist check only
        checks = {
            ValidationCheck.BLACKLIST: True,
        }
        
        is_valid, error_msg, _ = await self.validator.validate_command(
            interaction, None, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return
        
        # Calculate latencies
        ws_latency = round(self.bot.latency * 1000)

        # Measure response time
        start_time = time.perf_counter()
        await interaction.response.defer(thinking=True)
        end_time = time.perf_counter()
        response_time = round((end_time - start_time) * 1000)

        # Ping display
        from src.components.utility import PingView
        
        view = PingView(ws_latency, response_time)
        await interaction.followup.send(view=view)


async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))
