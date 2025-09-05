import discord
from discord import app_commands
from discord.ext import commands
import time
import pytz
from src.utils.command_validation import CommandValidator, ValidationCheck
from src.localization import get_translator, get_i18n


class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_service = bot.data_service
        self.validator = CommandValidator(bot)
        self.i18n = get_i18n()

    @app_commands.command(
        name="help", description="Display help information about the bot"
    )
    async def help_command(self, interaction: discord.Interaction):
        server_id = str(interaction.guild.id)
        translator = await get_translator(server_id, self.data_service)
        
        if await self.data_service.is_blacklisted(server_id):
            from src.components.general import BlacklistedServerView
            view = BlacklistedServerView(translator)
            await interaction.response.send_message(view=view, ephemeral=True)
            return
        
        from src.components.general import HelpView
        
        view = HelpView(translator)
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

        server_id = str(interaction.guild.id)
        translator = await get_translator(server_id, self.data_service)
        
        from src.components.general import PingView
        
        view = PingView(ws_latency, response_time, translator)
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
            
            server_id = str(interaction.guild.id)
            translator = await get_translator(server_id, self.data_service)
            
            from src.components.timezone import TimezoneInvalidView
            view = TimezoneInvalidView(timezone, suggestion, translator)
            await interaction.response.send_message(view=view, ephemeral=True)
            return
        
        server_id = str(interaction.guild.id)
        
        server = await self.data_service.get_server(server_id)
        if not server:
            server = await self.data_service.add_server(interaction.guild)
        
        await self.data_service.set_server_timezone(server_id, timezone, auto_detected=False)
        
        translator = await get_translator(server_id, self.data_service)
        from src.components.timezone import TimezoneChangeSuccessView
        view = TimezoneChangeSuccessView(timezone, translator)
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
        
        server_id = str(interaction.guild.id)
        translator = await get_translator(server_id, self.data_service)
        
        timezones = self.data_service.get_timezones_list()
        
        from src.components.timezone import TimezoneListView
        view = TimezoneListView(timezones, translator)
        await interaction.response.send_message(view=view)

    language_group = app_commands.Group(
        name="language",
        description="Manage server language preferences"
    )

    @language_group.command(
        name="list",
        description="Display all supported languages"
    )
    async def language_list(
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
        
        # Get translator for the current server
        server_id = str(interaction.guild.id)
        translator = await get_translator(server_id, self.data_service)
        
        # Get available languages
        languages = self.i18n.get_available_languages()
        current_language = await self.data_service.get_server_language(server_id) or "en"
        
        # Use the language list view
        from src.components.general import LanguageListView
        view = LanguageListView(languages, current_language, translator)
        await interaction.response.send_message(view=view)

    @language_group.command(
        name="change",
        description="Change the language for your server"
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        language="Select the language for your server"
    )
    @app_commands.choices(language=[
        app_commands.Choice(name="English", value="en"),
        app_commands.Choice(name="Danish (Dansk)", value="da"),
    ])
    async def language_change(
        self,
        interaction: discord.Interaction,
        language: app_commands.Choice[str]
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
        
        server_id = str(interaction.guild.id)
        
        # Get current language for translation
        current_language = await self.data_service.get_server_language(server_id) or "en"
        translator = await get_translator(server_id, self.data_service)
        
        # Get the selected language from the Choice
        selected_language = language.value
        available_languages = self.i18n.get_available_languages()
        
        # Check if already set to this language
        if current_language == selected_language:
            from src.components.general import LanguageAlreadySetView
            view = LanguageAlreadySetView(available_languages[selected_language], translator)
            await interaction.response.send_message(view=view, ephemeral=True)
            return
        
        # Get server and create if doesn't exist
        server = await self.data_service.get_server(server_id)
        if not server:
            server = await self.data_service.add_server(interaction.guild)
        
        # Set the language
        await self.data_service.set_server_language(server_id, selected_language)
        
        # Get new translator with the new language
        new_translator = await get_translator(server_id, self.data_service)
        
        # Send success message in the new language
        from src.components.general import LanguageChangeSuccessView
        view = LanguageChangeSuccessView(available_languages[selected_language], new_translator)
        await interaction.response.send_message(view=view)


async def setup(bot):
    await bot.add_cog(GeneralCommands(bot))