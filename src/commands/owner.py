import discord
from discord import app_commands
from discord.ext import commands
from src.utils.logger import logger, LogArea


class OwnerCommands(
    commands.GroupCog, group_name="owner", description="Owner-only management commands"
):
    def __init__(self, bot):
        self.bot = bot
        self.data_service = bot.data_service
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if user is the bot owner (using OWNER_ID from config)"""
        if not self.bot.is_owner(interaction.user):
            from src.components.owner import OwnerOnlyView
            view = OwnerOnlyView()
            await interaction.response.send_message(view=view, ephemeral=True)
            return False
        return True
    
    # Create subgroups
    admin_group = app_commands.Group(
        name="admin",
        description="Manage bot administrators",
        parent=None
    )
    
    recache_group = app_commands.Group(
        name="recache",
        description="Recache bot configuration",
        parent=None
    )
    
    @admin_group.command(
        name="list",
        description="List all bot administrators"
    )
    async def admin_list(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        
        admins = await self.data_service.get_admins()
        
        if not admins:
            from src.components.owner import NoAdminsView
            view = NoAdminsView()
            await interaction.followup.send(view=view)
            return
        
        from src.components.owner import AdminListView
        view = AdminListView(admins, self.bot)
        await interaction.followup.send(view=view)
    
    @admin_group.command(
        name="add",
        description="Add a new bot administrator"
    )
    @app_commands.describe(
        user_id="Discord user ID to add as admin"
    )
    async def admin_add(self, interaction: discord.Interaction, user_id: str):
        await interaction.response.defer(thinking=True)
        
        try:
            # Don't allow adding self as admin if already owner
            if str(interaction.user.id) == user_id:
                from src.components.owner import AdminAddSelfView
                view = AdminAddSelfView()
                await interaction.followup.send(view=view)
                return
            
            success = await self.data_service.add_admin(user_id)
            
            if success:
                # Try to get username for display
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    username = str(user)
                except:
                    username = "Unknown User"
                
                from src.components.owner import AdminAddSuccessView
                view = AdminAddSuccessView(username, user_id)
                await interaction.followup.send(view=view)
            else:
                from src.components.owner import AdminAddAlreadyView
                view = AdminAddAlreadyView(user_id)
                await interaction.followup.send(view=view)
                
        except Exception as e:
            logger.error(LogArea.COMMANDS, f"Error adding admin: {e}")
            from src.components.errors import ErrorView
            view = ErrorView("❌ **Failed to Add Admin**", f"An error occurred: {str(e)}")
            await interaction.followup.send(view=view)
    
    @admin_group.command(
        name="remove",
        description="Remove a bot administrator"
    )
    @app_commands.describe(
        user_id="Discord user ID to remove from admins"
    )
    async def admin_remove(self, interaction: discord.Interaction, user_id: str):
        await interaction.response.defer(thinking=True)
        
        if await self.data_service.remove_admin(user_id):
            from src.components.owner import AdminRemoveSuccessView
            view = AdminRemoveSuccessView(user_id)
            await interaction.followup.send(view=view)
        else:
            from src.components.owner import AdminRemoveNotFoundView
            view = AdminRemoveNotFoundView(user_id)
            await interaction.followup.send(view=view)
    
    @recache_group.command(
        name="config",
        description="Recache bot configuration from database"
    )
    async def recache_config(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        
        try:
            # Reload admin configuration and other bot settings
            await self.data_service.reload_admins_cache()
            
            # Get admin count
            admin_count = len(await self.data_service.get_admins())
            
            from src.components.owner import ConfigReloadSuccessView
            view = ConfigReloadSuccessView(admin_count)
            await interaction.followup.send(view=view)
            
        except Exception as e:
            logger.error(LogArea.COMMANDS, f"Error reloading config: {e}")
            from src.components.owner import ConfigReloadErrorView
            view = ConfigReloadErrorView(str(e))
            await interaction.followup.send(view=view)


async def setup(bot):
    # Owner commands require both OWNER_ID and GUILD_ID
    if bot.config.owner_id and bot.config.guild_id:
        await bot.add_cog(OwnerCommands(bot), guild=discord.Object(id=bot.config.guild_id))