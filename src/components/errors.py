"""
View Display for Error Handling
"""

import discord
from typing import Optional
from src.utils.footer import add_footer


class ErrorView(discord.ui.LayoutView):
    """View for error messages"""
    
    def __init__(self, title: str, description: str, translator, error_id: Optional[str] = None):
        super().__init__()
        
        content = f"{title}\n\n{description}"
        
        if error_id:
            content += f"\n\nError ID: `{error_id}`"
        
        content = add_footer(content, translator)
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class MissedClearView(discord.ui.LayoutView):
    """View for missed clear notification with Clear Now button"""
    
    def __init__(self, translator, channel: discord.TextChannel, message_clearing_service, bot):
        super().__init__()
        self.channel = channel
        self.message_clearing_service = message_clearing_service
        self.translator = translator
        self.bot = bot
        
        # Get the main notification text without footer
        main_text = translator.get("errors.missed_clear_notification")
        
        # Get the footer text separately
        from src.config import get_global_config
        config = get_global_config()
        footer_text = f"**{translator.get('components.powered_by', bot_name=config.bot_name)}**"
        
        # Create Clear Now button
        clear_button = discord.ui.Button(
            label=translator.get("components.buttons.clear_now"),
            style=discord.ButtonStyle.primary
        )
        clear_button.callback = self.clear_now_callback
        
        # Create action row with the button
        action_row = discord.ui.ActionRow(clear_button)
        
        # Add text display, button, and footer to container with yellow accent color
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=main_text),
            action_row,
            discord.ui.TextDisplay(content=footer_text),
            accent_color=discord.Color.yellow().value
        )
        self.add_item(container)
    
    async def clear_now_callback(self, interaction: discord.Interaction):
        """Handle the Clear Now button click"""
        from src.utils.command_validation import CommandValidator, ValidationCheck
        
        # Create validator and perform checks
        validator = CommandValidator(self.bot)
        
        # Check for manage_messages permission, blacklist, and bot permissions
        checks = {
            ValidationCheck.BLACKLIST: True,
            ValidationCheck.USER_PERMISSIONS: "manage_messages",
            ValidationCheck.BOT_PERMISSIONS: True,
            ValidationCheck.CHANNEL_SUBSCRIBED: True
        }
        
        is_valid, error_msg, _ = await validator.validate_command(
            interaction, 
            target_channel=self.channel,
            checks=checks
        )
        
        if not is_valid:
            await validator.send_validation_error(interaction, error_msg, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Execute the channel clear
        await self.message_clearing_service.execute_channel_message_clear(self.channel)
        
        # Send confirmation message
        await interaction.followup.send(
            self.translator.get("components.messages.channel_cleared_manually"),
            ephemeral=True
        )