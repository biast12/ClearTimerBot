import discord

async def notify_missed_clear(channel, job_id):
    from utils.clear_channel_messages import clear_channel_messages

    class ClearChannelView(discord.ui.View):
        def __init__(self, job_id):
            super().__init__(timeout=60)  # Timeout after 60 seconds
            self.job_id = job_id

        @discord.ui.button(label="Yes, clear the channel messages now", style=discord.ButtonStyle.danger)
        async def clear_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if not interaction.user.guild_permissions.manage_messages:
                await interaction.response.send_message("You do not have permission to manage messages.", ephemeral=True)
                return
            await interaction.response.defer()  # Defer the interaction response
            await clear_channel_messages(channel)
            await interaction.followup.send("Channel messages have been cleared.", ephemeral=True)
            self.stop()

        @discord.ui.button(label="No, do not clear the channel messages now", style=discord.ButtonStyle.secondary)
        async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if not interaction.user.guild_permissions.manage_messages:
                await interaction.response.send_message("You do not have permission to manage messages.", ephemeral=True)
                return
            await interaction.response.defer()  # Defer the interaction response
            await interaction.followup.send("Channel messages will not be cleared.", ephemeral=True)
            await interaction.message.delete()  # Delete the original message
            self.stop()

    await channel.send(
        "The bot was down when it should have cleared the channel messages. Would you like to clear the messages now?",
        view=ClearChannelView(job_id)
    )