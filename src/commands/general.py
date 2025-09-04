import discord
from discord import app_commands
from discord.ext import commands
import time
import pytz
from src.utils.command_validation import CommandValidator, ValidationCheck


class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_service = bot.data_service
        self.validator = CommandValidator(bot)

    @app_commands.command(
        name="help", description="Display help information about the bot"
    )
    async def help_command(self, interaction: discord.Interaction):
        server_id = str(interaction.guild.id)
        if await self.data_service.is_blacklisted(server_id):
            from src.components.general import BlacklistedServerView
            view = BlacklistedServerView()
            await interaction.response.send_message(view=view, ephemeral=True)
            return
        
        from src.components.general import HelpView
        
        view = HelpView()
        await interaction.response.send_message(view=view)

    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        checks = {
            ValidationCheck.BLACKLIST: True,
        }
        
        is_valid, error_msg, _ = await self.validator.validate_command(
            interaction, None, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return
        
        ws_latency = round(self.bot.latency * 1000)

        start_time = time.perf_counter()
        await interaction.response.defer(thinking=True)
        end_time = time.perf_counter()
        response_time = round((end_time - start_time) * 1000)

        from src.components.general import PingView
        
        view = PingView(ws_latency, response_time)
        await interaction.followup.send(view=view)

    timezone_group = app_commands.Group(
        name="timezone",
        description="Manage server timezone preferences"
    )

    @timezone_group.command(
        name="change",
        description="Change the default timezone for your server"
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        timezone="The timezone to set (e.g., America/New_York, Europe/London, or abbreviation like EST)"
    )
    async def timezone_change(
        self,
        interaction: discord.Interaction,
        timezone: str
    ):
        checks = {
            ValidationCheck.BLACKLIST: True,
        }
        
        is_valid, error_msg, _ = await self.validator.validate_command(
            interaction, None, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return
        
        timezone_mappings = self.data_service.get_timezones_list()
        if timezone.upper() in timezone_mappings:
            timezone = timezone_mappings[timezone.upper()]
        
        try:
            pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            all_timezones = pytz.all_timezones
            suggestion = None
            timezone_lower = timezone.lower()
            
            for tz in all_timezones:
                if timezone_lower in tz.lower():
                    suggestion = tz
                    break
            
            from src.components.timezone import InvalidTimezoneView
            view = InvalidTimezoneView(timezone, suggestion)
            await interaction.response.send_message(view=view, ephemeral=True)
            return
        
        server_id = str(interaction.guild.id)
        
        server = await self.data_service.get_server(server_id)
        if not server:
            server = await self.data_service.add_server(interaction.guild)
        
        await self.data_service.set_server_timezone(server_id, timezone, auto_detected=False)
        
        from src.components.timezone import TimezoneChangeView
        view = TimezoneChangeView(timezone, auto_detected=False)
        await interaction.response.send_message(view=view)

    @timezone_group.command(
        name="list",
        description="List available timezones from the configuration"
    )
    async def timezone_list(
        self,
        interaction: discord.Interaction
    ):
        checks = {
            ValidationCheck.BLACKLIST: True,
        }
        
        is_valid, error_msg, _ = await self.validator.validate_command(
            interaction, None, checks
        )
        
        if not is_valid:
            await self.validator.send_validation_error(interaction, error_msg)
            return
        
        timezones = self.data_service.get_timezones_list()
        
        from src.components.timezone import TimezoneListView
        view = TimezoneListView(timezones)
        await interaction.response.send_message(view=view)


async def setup(bot):
    await bot.add_cog(GeneralCommands(bot))