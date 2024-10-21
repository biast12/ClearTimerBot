from discord import app_commands
from discord.ext import commands
from utils.handle_error import handle_error
from utils.is_owner import is_owner
from utils.logger import logger

class TestCommandsCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="test_commands", description="Test all commands to see if they work (Bot owner only)")
    @is_owner()
    async def test_commands(self, interaction):
        """
        Test all commands to see if they work.

        Args:
            interaction (discord.Interaction): The interaction that triggered the command.
        """
        failed_commands = []
        for command in self.bot.tree.walk_commands():
            try:
                # Simulate command execution without invoking the callback
                await command._check_can_run(interaction)
            except Exception as e:
                failed_commands.append((command.name, str(e)))
                logger.error(f"Command {command.name} failed: {e}")

        if failed_commands:
            message = "Some commands failed:\n" + "\n".join([f"{name}: {error}" for name, error in failed_commands])
        else:
            message = "All commands executed successfully."

        # Respond to the interaction only once
        await interaction.response.send_message(message, ephemeral=True)

    @test_commands.error
    async def test_commands_error(self, interaction, error):
        if not interaction.response.is_done():
            await handle_error(interaction, error, 'test_commands')

async def setup(bot):
    await bot.add_cog(TestCommandsCommand(bot))