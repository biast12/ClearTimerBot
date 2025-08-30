import discord
from discord import app_commands
from discord.ext import commands
import time


class UtilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        # Calculate latencies
        ws_latency = round(self.bot.latency * 1000)
        
        # Measure response time
        start_time = time.perf_counter()
        await interaction.response.defer(thinking=True)
        end_time = time.perf_counter()
        response_time = round((end_time - start_time) * 1000)
        
        # Create response embed
        embed = discord.Embed(
            title="🏓 Pong!",
            color=self._get_latency_color(ws_latency)
        )
        
        embed.add_field(
            name="WebSocket Latency",
            value=f"{ws_latency}ms",
            inline=True
        )
        
        embed.add_field(
            name="Response Time",
            value=f"{response_time}ms",
            inline=True
        )
        
        embed.add_field(
            name="Status",
            value=self._get_status_emoji(ws_latency),
            inline=True
        )
        
        await interaction.followup.send(embed=embed)
    
    def _get_latency_color(self, latency: int) -> discord.Color:
        if latency < 100:
            return discord.Color.green()
        elif latency < 300:
            return discord.Color.yellow()
        else:
            return discord.Color.red()
    
    def _get_status_emoji(self, latency: int) -> str:
        if latency < 100:
            return "🟢 Excellent"
        elif latency < 200:
            return "🟡 Good"
        elif latency < 300:
            return "🟠 Fair"
        else:
            return "🔴 Poor"


async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))