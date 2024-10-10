from discord import app_commands
from discord.ext import commands
from utils.handle_error import handle_error
from utils.is_owner import is_owner
from utils.utils import load_blacklist

class OwnerHelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="owner_help", description="Display available bot owner only commands (Bot owner only)")
    @is_owner()
    async def owner_help(self, interaction):
        blacklist = load_blacklist()

        server_id = str(interaction.guild.id)
    
        if server_id in blacklist:
            await interaction.response.send_message(f"Server {server_id} is blacklisted and cannot use commands from this bot", ephemeral=True)
            return
        
        help_message = (
            " **Owner-Only Commands:**\n"
            "`/list` - List all servers and channels subscribed to message deletion\n"
            "`/blacklist_add [server_id]` - Add a server to the blacklist\n"
            "`/blacklist_remove [server_id]` - Remove a server from the blacklist\n"
            "`/blacklist_list` - List all blacklisted servers\n"
            "`/owner_help` - Display this message\n\n"
            "For more help, join our help server: [Help Server](https://discord.com/invite/ERFffj9Qs7)"
        )
        await interaction.response.send_message(help_message)

    # Error handler for owner_help command
    @owner_help.error
    async def owner_help_error(self, interaction, error):
        await handle_error(interaction, error, 'owner_help')

async def setup(bot):
    await bot.add_cog(OwnerHelpCommand(bot), override=True)