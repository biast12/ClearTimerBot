import discord
from discord import app_commands
from discord.ext import commands
from src.utils.logger import logger, LogArea
import asyncio
from typing import Optional


class OwnerCommands(
    commands.GroupCog, group_name="owner", description="Owner-only management commands"
):
    def __init__(self, bot):
        self.bot = bot
        self.data_service = bot.data_service
    
    async def _check_owner_permission(self, interaction: discord.Interaction) -> bool:
        """Check if user is the bot owner (using OWNER_ID from config)"""
        if not self.bot.is_owner(interaction.user):
            from src.components.owner import OwnerOnlyView
            view = OwnerOnlyView()
            if not interaction.response.is_done():
                await interaction.response.send_message(view=view, ephemeral=True)
            else:
                await interaction.followup.send(view=view, ephemeral=True)
            return False
        return True
    
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
    
    shard_group = app_commands.Group(
        name="shard",
        description="Manage bot shards",
        parent=None
    )
    
    @admin_group.command(
        name="list",
        description="List all bot administrators"
    )
    async def admin_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        if not await self._check_owner_permission(interaction):
            return
        
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
        await interaction.response.defer(ephemeral=True)
        
        if not await self._check_owner_permission(interaction):
            return
        
        try:
            if str(interaction.user.id) == user_id:
                from src.components.owner import AdminAddSelfView
                view = AdminAddSelfView()
                await interaction.followup.send(view=view)
                return
            
            success = await self.data_service.add_admin(user_id)
            
            if success:
                try:
                    cache_key = f"discord:user:{user_id}"
                    user = await self.data_service._cache.get(cache_key)
                    
                    if not user:
                        user = await self.bot.fetch_user(int(user_id))
                        await self.data_service._cache.set(cache_key, user, cache_level="warm", ttl=1800)
                    
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
        await interaction.response.defer(ephemeral=True)
        
        if not await self._check_owner_permission(interaction):
            return
        
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
        await interaction.response.defer(ephemeral=True)
        
        if not await self._check_owner_permission(interaction):
            return
        
        try:
            await self.data_service.reload_admins_cache()
            admin_count = len(await self.data_service.get_admins())
            
            from src.components.owner import ConfigReloadSuccessView
            view = ConfigReloadSuccessView(admin_count)
            await interaction.followup.send(view=view)
            
        except Exception as e:
            logger.error(LogArea.COMMANDS, f"Error reloading config: {e}")
            from src.components.owner import ConfigReloadErrorView
            view = ConfigReloadErrorView(str(e))
            await interaction.followup.send(view=view)
    
    
    @shard_group.command(
        name="reload",
        description="Reload all shards or a specific shard"
    )
    @app_commands.describe(
        shard_id="Specific shard ID to reload (leave empty to reload all)"
    )
    async def shard_reload(self, interaction: discord.Interaction, shard_id: Optional[int] = None):
        await interaction.response.defer(ephemeral=True)
        
        if not await self._check_owner_permission(interaction):
            return
        
        try:
            if self.bot.shard_id is None and shard_id is not None:
                from src.components.owner import ShardNotShardedView
                view = ShardNotShardedView()
                await interaction.followup.send(view=view)
                return
            
            if shard_id is not None:
                if self.bot.shard_count and (shard_id < 0 or shard_id >= self.bot.shard_count):
                    from src.components.owner import ShardInvalidIdView
                    view = ShardInvalidIdView(shard_id, self.bot.shard_count)
                    await interaction.followup.send(view=view)
                    return
                
                from src.components.owner import ShardReloadSingleView
                view = ShardReloadSingleView(shard_id)
                await interaction.followup.send(view=view)
                
                if self.bot.shard_id == shard_id:
                    logger.info(LogArea.COMMANDS, f"Reloading current shard {shard_id} (self-restart)")
                    self.bot.restart_requested = True
                    asyncio.create_task(self._delayed_shutdown())
                else:
                    logger.info(LogArea.COMMANDS, f"Reload requested for shard {shard_id}")
                    from src.components.owner import ShardReloadSignalView
                    view = ShardReloadSignalView(shard_id)
                    await interaction.edit_original_response(view=view)
            else:
                from src.components.owner import ShardRestartView
                view = ShardRestartView()
                await interaction.followup.send(view=view)
                
                logger.info(LogArea.COMMANDS, "Reloading all shards")
                self.bot.restart_requested = True
                asyncio.create_task(self._delayed_shutdown())
                
        except Exception as e:
            logger.error(LogArea.COMMANDS, f"Error reloading shard: {e}")
            from src.components.owner import ShardReloadFailedView
            view = ShardReloadFailedView(str(e))
            await interaction.followup.send(view=view)
    
    
    @shard_group.command(
        name="status",
        description="View current shard status"
    )
    async def shard_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        if not await self._check_owner_permission(interaction):
            return
        
        try:
            from src.components.owner import ShardStatusCompleteView
            view = ShardStatusCompleteView(self.bot)
            await interaction.followup.send(view=view)
            
        except Exception as e:
            logger.error(LogArea.COMMANDS, f"Error getting shard status: {e}")
            from src.components.errors import ErrorView
            view = ErrorView("❌ **Failed to Get Status**", f"An error occurred: {str(e)}")
            await interaction.followup.send(view=view)
    
    
    async def _delayed_shutdown(self):
        """Gracefully shutdown the bot after a delay"""
        await asyncio.sleep(2)
        logger.info(LogArea.COMMANDS, "Initiating graceful shutdown for restart...")
        await self.bot.close()


async def setup(bot):
    if bot.config.owner_id and bot.config.guild_id:
        await bot.add_cog(OwnerCommands(bot), guild=discord.Object(id=bot.config.guild_id))