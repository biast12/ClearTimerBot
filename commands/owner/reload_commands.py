import os
from discord import app_commands
from discord.ext import commands
from utils.handle_error import handle_error
from utils.is_owner import is_owner
from utils.logger import logger

class ReloadCommandsCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='reload_commands', description="Reloads all synced commands (Bot owner only)")
    @is_owner()
    async def reload_commands(self, interaction):
        try:
            from utils.sync import sync_commands, sync_owner_commands

            logger.info("Reloading synced commands...")
            await interaction.response.send_message("Reloading synced commands...", ephemeral=True)
            
            # Reloads all commands globally
            self.bot.tree.clear_commands(guild=None)
            await self.bot.tree.sync(guild=None)
            await sync_commands(self.bot)
            
            # Reloads all commands for the bot owner guild
            OWNER_ID = int(os.getenv("OWNER_ID"))
            GUILD_ID = int(os.getenv("GUILD_ID"))
            
            if GUILD_ID and OWNER_ID:
                bot_owner_guild = self.bot.get_guild(GUILD_ID)
                if bot_owner_guild:
                    self.bot.tree.clear_commands(guild=bot_owner_guild)
                    await self.bot.tree.sync(guild=bot_owner_guild)
                    await sync_owner_commands(self.bot, GUILD_ID)

            # Edit the original response message
            await interaction.edit_original_response(content="All synced commands reloaded successfully.")
        except Exception as e:
            logger.error(f"Failed to reload commands: {e}")
            await interaction.followup.send(f"Failed to reload commands: {e}", ephemeral=True)

    # Error handler for reload_commands command
    @reload_commands.error
    async def reload_commands_error(self, interaction, error):
        await handle_error(interaction, error, 'reload_commands', True)

async def setup(bot):
    await bot.add_cog(ReloadCommandsCommand(bot))