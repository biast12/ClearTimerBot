import discord
from discord import app_commands
from discord.ext import commands
import time


class UtilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help", description="Display help information about the bot"
    )
    async def help_command(self, interaction: discord.Interaction):
        # Use Components v2 for help display
        from src.components.utility import HelpView
        
        view = HelpView()
        await interaction.response.send_message(view=view)

    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        # Calculate latencies
        ws_latency = round(self.bot.latency * 1000)

        # Measure response time
        start_time = time.perf_counter()
        await interaction.response.defer(thinking=True)
        end_time = time.perf_counter()
        response_time = round((end_time - start_time) * 1000)

        # Use Components v2 for ping display
        from src.components.utility import PingView
        
        view = PingView(ws_latency, response_time)
        await interaction.followup.send(view=view)


async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))
