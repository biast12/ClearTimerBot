import os
from discord import app_commands
from discord.ext import commands
from utils.handle_error import handle_error
from utils.is_owner import is_owner
from utils.logger import logger
from utils.data_manager import load_blacklist, save_blacklist

class BlacklistRemoveCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='blacklist_remove', description="Remove a server from the blacklist (Bot owner only)")
    @is_owner()
    async def blacklist_remove(self, interaction, server_id: str):
        """
        Remove a server from the blacklist.

        Args:
            interaction (discord.Interaction): The interaction that triggered the command.
            server_id (str): The ID of the server to remove from the blacklist.
        """
        blacklist = load_blacklist()

        server_id = str(server_id)

        if server_id not in blacklist:
            await interaction.response.send_message(f"Server {server_id} is not in the blacklist.", ephemeral=True)
            return
    
        blacklist.remove(server_id)
        save_blacklist(blacklist)
        await interaction.response.send_message(f"Server {server_id} has been removed from the blacklist.", ephemeral=True)
        logger.info(f'Removed server {server_id} from blacklist')
    
    # Error handler for blacklist_remove command
    @blacklist_remove.error
    async def blacklist_remove_error(self, interaction, error):
        await handle_error(interaction, error, 'blacklist_remove', True)

async def setup(bot):
    OWNER_ID = os.getenv("OWNER_ID")
    GUILD_ID = os.getenv("GUILD_ID")
    if GUILD_ID and OWNER_ID:
        guild = bot.get_guild(int(GUILD_ID))
        if guild:
            await bot.add_cog(BlacklistRemoveCommand(bot), guild=guild, override=True)
        else:
            print(f"Guild with ID {GUILD_ID} not found.")
    else:
        print("GUILD_ID not set in environment variables.")