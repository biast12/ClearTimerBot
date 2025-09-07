"""
View Display for Owner Commands with Localization
"""

import discord
import os
from src.localization import get_translator


class OwnerOnlyView(discord.ui.LayoutView):
    """View for owner-only restriction message"""
    
    def __init__(self, translator=None):
        super().__init__()
        
        # Use provided translator or fallback to hardcoded English
        if translator:
            title = translator.get("commands.owner.permission_denied.title")
            description = translator.get("commands.owner.permission_denied.description")
            content = f"🔒 **{title}**\n\n{description}"
        else:
            content = (
                "🔒 **Owner Only**\n\n"
                "This command is restricted to the bot owner."
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class NoAdminsView(discord.ui.LayoutView):
    """View for no admins found"""
    
    def __init__(self, translator=None):
        super().__init__()
        
        if translator:
            title = translator.get("commands.owner.admin.list.no_admins_title")
            description = translator.get("commands.owner.admin.list.no_admins_description")
            hint = translator.get("commands.owner.admin.list.no_admins_hint")
            content = f"📋 **{title}**\n\n{description}\n\n_{hint}_"
        else:
            content = (
                "📋 **No Admins Configured**\n\n"
                "There are no administrators configured.\n\n"
                "_Use `/owner admin add` to add administrators_"
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.greyple().value
        )
        self.add_item(container)


class AdminListView(discord.ui.LayoutView):
    """View for listing all admins"""
    
    def __init__(self, admins: set, bot, translator=None):
        super().__init__()
        
        if translator:
            title = translator.get("commands.owner.admin.list.title")
            content = f"👥 **{title}**\n\n"
        else:
            content = "👥 **Bot Administrators**\n\n"
        
        for user_id in sorted(admins):
            # Try to get current username from bot
            try:
                user = bot.get_user(int(user_id))
                current_name = str(user) if user else f"User {user_id}"
            except:
                current_name = f"User {user_id}"
            
            content += f"• **{current_name}**\n"
            content += f"  ID: `{user_id}`\n"
            content += f"  Mention: <@{user_id}>\n\n"
        
        admin_count = len(admins)
        admin_text = "administrator" if admin_count == 1 else "administrators"
        
        if translator:
            total_text = translator.get("commands.owner.admin.list.total", 
                                       count=admin_count, 
                                       admin_text=admin_text)
            content += f"_{total_text}_"
        else:
            content += f"_Total: {admin_count} {admin_text}_"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value
        )
        self.add_item(container)


class AdminAddSuccessView(discord.ui.LayoutView):
    """View for successful admin addition"""
    
    def __init__(self, username: str, user_id: str, translator=None):
        super().__init__()
        
        if translator:
            title = translator.get("commands.owner.admin.add.success_title")
            description = translator.get("commands.owner.admin.add.success_description", username=username)
            user_id_text = translator.get("commands.owner.admin.add.success_user_id", user_id=user_id)
            mention_text = translator.get("commands.owner.admin.add.success_mention", user_id=user_id)
            note = translator.get("commands.owner.admin.add.success_note")
            
            content = (
                f"✅ **{title}**\n\n"
                f"{description}\n\n"
                f"**{user_id_text}**\n"
                f"**{mention_text}**\n\n"
                f"_{note}_"
            )
        else:
            content = (
                f"✅ **Administrator Added**\n\n"
                f"Successfully added **{username}** as a bot administrator.\n\n"
                f"**User ID:** `{user_id}`\n"
                f"**Mention:** <@{user_id}>\n\n"
                "_This user can now use admin commands_"
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class AdminAddAlreadyView(discord.ui.LayoutView):
    """View for admin already exists"""
    
    def __init__(self, user_id: str, translator=None):
        super().__init__()
        
        if translator:
            title = translator.get("commands.owner.admin.add.already_title")
            description = translator.get("commands.owner.admin.add.already_description", user_id=user_id)
            content = f"⚠️ **{title}**\n\n{description}\nMention: <@{user_id}>"
        else:
            content = (
                f"⚠️ **Already Administrator**\n\n"
                f"User `{user_id}` is already a bot administrator.\n"
                f"Mention: <@{user_id}>"
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.yellow().value
        )
        self.add_item(container)


class AdminAddSelfView(discord.ui.LayoutView):
    """View for trying to add yourself as admin when you're the owner"""
    
    def __init__(self, translator=None):
        super().__init__()
        
        if translator:
            title = translator.get("commands.owner.admin.add.self_title")
            description = translator.get("commands.owner.admin.add.self_description")
            note = translator.get("commands.owner.admin.add.self_note")
            content = f"⚠️ **{title}**\n\n{description}\n\n_{note}_"
        else:
            content = (
                "⚠️ **Already Owner**\n\n"
                "You are the bot owner and already have full permissions.\n\n"
                "_No need to add yourself as an administrator_"
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.yellow().value
        )
        self.add_item(container)


class AdminRemoveSuccessView(discord.ui.LayoutView):
    """View for successful admin removal"""
    
    def __init__(self, user_id: str, translator=None):
        super().__init__()
        
        if translator:
            title = translator.get("commands.owner.admin.remove.success_title")
            description = translator.get("commands.owner.admin.remove.success_description", user_id=user_id)
            previous = translator.get("commands.owner.admin.remove.success_previous", user_id=user_id)
            note = translator.get("commands.owner.admin.remove.success_note")
            
            content = (
                f"✅ **{title}**\n\n"
                f"{description}\n"
                f"{previous}\n\n"
                f"_{note}_"
            )
        else:
            content = (
                f"✅ **Administrator Removed**\n\n"
                f"Successfully removed `{user_id}` from administrators.\n"
                f"Previous admin: <@{user_id}>\n\n"
                "_This user can no longer use admin commands_"
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class AdminRemoveNotFoundView(discord.ui.LayoutView):
    """View for admin not found"""
    
    def __init__(self, user_id: str, translator=None):
        super().__init__()
        
        if translator:
            title = translator.get("commands.owner.admin.remove.not_found_title")
            description = translator.get("commands.owner.admin.remove.not_found_description", user_id=user_id)
            note = translator.get("commands.owner.admin.remove.not_found_note")
            
            content = (
                f"❌ **{title}**\n\n"
                f"{description}\n\n"
                f"_{note}_"
            )
        else:
            content = (
                f"❌ **Not an Administrator**\n\n"
                f"User `{user_id}` is not a bot administrator.\n\n"
                "_Cannot remove someone who isn't an admin_"
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)




class ShardReloadSingleView(discord.ui.LayoutView):
    """View for reloading a single shard"""
    
    def __init__(self, shard_id: int, translator=None):
        super().__init__()
        
        if translator:
            title = translator.get("commands.owner.shard.reload.single_title")
            description = translator.get("commands.owner.shard.reload.single_description", shard_id=shard_id)
            what_happens = translator.get("commands.owner.shard.reload.single_what_happens")
            note1 = translator.get("commands.owner.shard.reload.single_note_1")
            note2 = translator.get("commands.owner.shard.reload.single_note_2")
            note3 = translator.get("commands.owner.shard.reload.single_note_3")
            
            content = (
                f"🔄 **{title}**\n\n"
                f"{description}\n\n"
                f"**{what_happens}**\n"
                f"{note1}\n"
                f"{note2}\n"
                f"{note3}"
            )
        else:
            content = (
                f"🔄 **Reloading Single Shard**\n\n"
                f"Restarting shard {shard_id} only...\n\n"
                "**What happens:**\n"
                "• Only this specific shard restarts\n"
                "• Other shards continue running\n"
                "• Guilds on this shard temporarily offline"
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.yellow().value
        )
        self.add_item(container)




class ShardNotShardedView(discord.ui.LayoutView):
    """View for when bot is not sharded but shard reload is requested"""
    
    def __init__(self, translator=None):
        super().__init__()
        
        if translator:
            title = translator.get("commands.owner.shard.reload.not_sharded_title")
            description = translator.get("commands.owner.shard.reload.not_sharded_description")
            hint = translator.get("commands.owner.shard.reload.not_sharded_hint")
            
            content = (
                f"⚠️ **{title}**\n\n"
                f"{description}\n\n"
                f"_{hint}_"
            )
        else:
            content = (
                "⚠️ **Cannot Reload Shard**\n\n"
                "Bot is running in single-instance mode (not sharded).\n\n"
                "_Use `/owner shard reload` to reload the bot_"
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class ShardInvalidIdView(discord.ui.LayoutView):
    """View for invalid shard ID"""
    
    def __init__(self, shard_id: int, max_shard: int, translator=None):
        super().__init__()
        
        if translator:
            title = translator.get("commands.owner.shard.reload.invalid_id_title")
            description = translator.get("commands.owner.shard.reload.invalid_id_description", shard_id=shard_id)
            range_text = translator.get("commands.owner.shard.reload.invalid_id_range", max_shard=max_shard - 1)
            note = translator.get("commands.owner.shard.reload.invalid_id_note")
            
            content = (
                f"❌ **{title}**\n\n"
                f"{description}\n\n"
                f"**{range_text}**\n\n"
                f"_{note}_"
            )
        else:
            content = (
                f"❌ **Invalid Shard ID**\n\n"
                f"Shard ID `{shard_id}` is invalid.\n\n"
                f"**Valid Range:** 0 to {max_shard - 1}\n\n"
                "_Please specify a valid shard ID_"
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)


class ShardReloadSignalView(discord.ui.LayoutView):
    """View for reload signal sent to another shard"""
    
    def __init__(self, shard_id: int, translator=None):
        super().__init__()
        
        if translator:
            title = translator.get("commands.owner.shard.reload.signal_sent_title")
            description = translator.get("commands.owner.shard.reload.signal_sent_description", shard_id=shard_id)
            note = translator.get("commands.owner.shard.reload.signal_sent_note")
            manual = translator.get("commands.owner.shard.reload.signal_sent_manual")
            future = translator.get("commands.owner.shard.reload.signal_sent_future")
            
            content = (
                f"📡 **{title}**\n\n"
                f"{description}\n\n"
                f"**{note}**\n"
                f"{manual}\n\n"
                f"_{future}_"
            )
        else:
            content = (
                f"📡 **Reload Signal Sent**\n\n"
                f"Reload signal sent to shard {shard_id}.\n\n"
                "**Note:** Cross-shard communication is not yet implemented.\n"
                "Please restart the shard manually.\n\n"
                "_Future updates will enable automatic cross-shard reloading_"
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value
        )
        self.add_item(container)


class ShardReloadFailedView(discord.ui.LayoutView):
    """View for shard reload failure"""
    
    def __init__(self, error: str, translator=None):
        super().__init__()
        
        if translator:
            title = translator.get("commands.owner.shard.reload.failed_title")
            description = translator.get("commands.owner.shard.reload.failed_description")
            error_text = translator.get("commands.owner.shard.reload.failed_error", error=error)
            note = translator.get("commands.owner.shard.reload.failed_note")
            
            content = (
                f"❌ **{title}**\n\n"
                f"{description}\n\n"
                f"**{error_text}**\n\n"
                f"_{note}_"
            )
        else:
            content = (
                f"❌ **Reload Failed**\n\n"
                "Failed to reload shard.\n\n"
                f"**Error:** {error}\n\n"
                "_Please check the logs for more details_"
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value
        )
        self.add_item(container)




class ShardStatusCompleteView(discord.ui.LayoutView):
    """View for shard status"""
    
    def __init__(self, bot, translator=None):
        super().__init__()
        
        if translator:
            title = translator.get("commands.owner.shard.status.title")
            content = f"🔷 **{title}**\n\n"
            
            current_runtime = translator.get("commands.owner.shard.status.current_runtime")
            content += f"**{current_runtime}**\n"
        else:
            content = "🔷 **Shard Status**\n\n"
            content += "**Current Runtime:**\n"
        
        if bot.shard_id is not None:
            if translator:
                content += translator.get("commands.owner.shard.status.shard_info", 
                                         shard_id=bot.shard_id, 
                                         max_shard=bot.shard_count - 1) + "\n"
                content += translator.get("commands.owner.shard.status.total_shards", 
                                         count=bot.shard_count) + "\n"
                content += translator.get("commands.owner.shard.status.guilds_on_shard", 
                                         count=len(bot.guilds)) + "\n"
            else:
                content += f"• Shard: {bot.shard_id}/{bot.shard_count - 1}\n"
                content += f"• Total Shards: {bot.shard_count}\n"
                content += f"• Guilds on This Shard: {len(bot.guilds)}\n"
            
            # Get shard latency
            try:
                shard = bot.get_shard(bot.shard_id)
                latency = shard.latency if shard and shard.latency is not None else bot.latency
            except:
                latency = bot.latency
            
            if translator:
                content += translator.get("commands.owner.shard.status.latency", 
                                         latency=f"{latency * 1000:.2f}") + "\n"
            else:
                content += f"• Latency: {latency * 1000:.2f}ms\n"
        else:
            if translator:
                content += translator.get("commands.owner.shard.status.single_mode") + "\n"
                content += translator.get("commands.owner.shard.status.total_guilds", 
                                         count=len(bot.guilds)) + "\n"
                content += translator.get("commands.owner.shard.status.latency", 
                                         latency=f"{bot.latency * 1000:.2f}") + "\n"
            else:
                content += "• Mode: Single-instance (not sharded)\n"
                content += f"• Total Guilds: {len(bot.guilds)}\n"
                content += f"• Latency: {bot.latency * 1000:.2f}ms\n"
        
        pid = os.getpid()
        if translator:
            content += translator.get("commands.owner.shard.status.process_id", pid=pid) + "\n\n"
            
            available_commands = translator.get("commands.owner.shard.status.available_commands")
            cmd_reload_all = translator.get("commands.owner.shard.status.cmd_reload_all")
            cmd_reload_single = translator.get("commands.owner.shard.status.cmd_reload_single")
            cmd_status = translator.get("commands.owner.shard.status.cmd_status")
            
            content += f"**{available_commands}**\n"
            content += f"{cmd_reload_all}\n"
            content += f"{cmd_reload_single}\n"
            content += f"{cmd_status}"
        else:
            content += f"• Process ID: `{pid}`\n\n"
            content += "**Available Commands:**\n"
            content += "• `/owner shard reload` - Reload all shards\n"
            content += "• `/owner shard reload <id>` - Reload specific shard\n"
            content += "• `/owner shard status` - View this status"
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value
        )
        self.add_item(container)




class ShardRestartView(discord.ui.LayoutView):
    """View for restarting all shards"""
    
    def __init__(self, translator=None):
        super().__init__()
        
        if translator:
            title = translator.get("commands.owner.shard.reload.all_title")
            description = translator.get("commands.owner.shard.reload.all_description")
            what_happens = translator.get("commands.owner.shard.reload.all_what_happens")
            note1 = translator.get("commands.owner.shard.reload.all_note_1")
            note2 = translator.get("commands.owner.shard.reload.all_note_2")
            note3 = translator.get("commands.owner.shard.reload.all_note_3")
            note4 = translator.get("commands.owner.shard.reload.all_note_4")
            hint = translator.get("commands.owner.shard.reload.all_hint")
            
            content = (
                f"🔄 **{title}**\n\n"
                f"{description}\n\n"
                f"**{what_happens}**\n"
                f"{note1}\n"
                f"{note2}\n"
                f"{note3}\n"
                f"{note4}\n\n"
                f"_{hint}_"
            )
        else:
            content = (
                "🔄 **Reloading All Shards**\n\n"
                "Full bot reload initiated...\n\n"
                "**What happens:**\n"
                "• All shards shut down together\n"
                "• Shard manager restarts\n"
                "• All shards relaunch with fresh state\n"
                "• Bot offline for ~5-10 seconds\n\n"
                "_Use `/owner shard reload <id>` to reload single shard only_"
            )
        
        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.yellow().value
        )
        self.add_item(container)