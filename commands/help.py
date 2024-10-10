from discord import app_commands
from discord.ext import commands
from utils.handle_error import handle_error
from utils.utils import load_blacklist

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Display available commands")
    async def help(self, interaction):
        blacklist = load_blacklist()

        server_id = str(interaction.guild.id)
    
        if server_id in blacklist:
            await interaction.response.send_message(f"Server {server_id} is blacklisted and cannot use commands from this bot", ephemeral=True)
            return
        
        help_message = (
            " **Available Commands:**\n"
            "`/sub [timer] [target_channel]` - Subscribe a channel to message deletion\n"
            "- Timer syntax: `1d2h3m` for days, hours, and minutes or `HH:MM <timezone>` for specific times every day\n\n"
            "`/unsub [target_channel]` - Unsubscribe from message deletion\n"
            "`/next [target_channel]` - Check when the next message clear is scheduled\n"
            "`/ping` - Check the bot's latency\n"
            "`/help` - Display this message\n\n"
            "For more help, join our help server: [Help Server](https://discord.com/invite/ERFffj9Qs7)"
        )
        await interaction.response.send_message(help_message)

    @help.error
    async def help_error(self, interaction, error):
        await handle_error(interaction, error, 'help')

async def setup(bot):
    await bot.add_cog(HelpCommand(bot), override=True)