"""
View Display for Admin Commands with Localization
"""

import discord
from discord.ext import commands


class AdminOnlyView(discord.ui.LayoutView):
    """View for admin-only restriction message"""

    def __init__(self, translator):
        super().__init__()

        title = translator.get("commands.admin.permission_denied.title")
        description = translator.get("commands.admin.permission_denied.description")
        content = f"❌ **{title}**\n\n{description}"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class SimpleStatsView(discord.ui.LayoutView):
    """View for showing simple bot statistics"""

    def __init__(
        self,
        total_servers: int,
        total_channels: int,
        removed_servers: int,
        blacklisted_servers: int,
        error_count: int,
        translator,
    ):
        super().__init__()

        title = translator.get("commands.admin.stats.title")
        servers = translator.get("commands.admin.stats.servers", count=total_servers)
        channels = translator.get(
            "commands.admin.stats.subscribed_channels", count=total_channels
        )
        removed = translator.get(
            "commands.admin.stats.removed_servers", count=removed_servers
        )
        blacklisted = translator.get(
            "commands.admin.stats.blacklisted_servers", count=blacklisted_servers
        )
        errors = translator.get("commands.admin.stats.saved_errors", count=error_count)

        content = f"📊 **{title}**\n\n"
        content += f"**{servers}**\n"
        content += f"**{channels}**\n"
        content += f"**{removed}**\n"
        content += f"**{blacklisted}**\n"
        content += f"**{errors}**"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value,
        )
        self.add_item(container)


class ServerStatsView(discord.ui.LayoutView):
    """View for showing server-specific statistics"""

    def __init__(
        self,
        server_id: str,
        server_name: str,
        channel_count: int,
        is_blacklisted: bool,
        error_count: int,
        bot,
        channels: dict,
        translator,
    ):
        super().__init__()

        title = translator.get("commands.admin.stats.server_title")
        server_label = translator.get(
            "commands.admin.stats.server_name", name=server_name
        )
        server_id_label = translator.get("commands.admin.stats.server_id", id=server_id)
        channels_label = translator.get(
            "commands.admin.stats.subscribed_channels", count=channel_count
        )
        yes_status = translator.get("commands.admin.stats.blacklisted_yes")
        no_status = translator.get("commands.admin.stats.blacklisted_no")
        blacklisted_label = translator.get(
            "commands.admin.stats.blacklisted",
            status=yes_status if is_blacklisted else no_status,
        )
        errors_label = translator.get("commands.admin.stats.errors", count=error_count)

        content = f"📊 **{title}**\n\n"
        content += f"**{server_label}**\n"
        content += f"**{server_id_label}**\n"
        content += f"**{channels_label}**\n"
        content += f"**{blacklisted_label}**\n"
        content += f"**{errors_label}**\n"

        if channels:
            channels_header = translator.get("commands.admin.stats.channels_label")
            content += f"\n**{channels_header}**\n"
            for channel_id, timer_data in list(channels.items())[:10]:
                channel = bot.get_channel(int(channel_id))
                unknown_channel = translator.get("commands.admin.stats.unknown_channel")
                channel_name = f"#{channel.name}" if channel else unknown_channel
                content += f"• {channel_name} - `{timer_data.timer}`\n"

            if len(channels) > 10:
                more_text = translator.get(
                    "commands.admin.stats.more_channels", count=len(channels) - 10
                )
                content += f"_{more_text}_"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=(
                discord.Color.red().value
                if is_blacklisted
                else discord.Color.blue().value
            ),
        )
        self.add_item(container)


class ServerNotFoundView(discord.ui.LayoutView):
    """View for when a server is not found in the database"""

    def __init__(self, server_id: str, translator):
        super().__init__()

        title = translator.get("commands.admin.stats.not_found_title")
        description = translator.get(
            "commands.admin.stats.not_found_description", server_id=server_id
        )
        note = translator.get("commands.admin.stats.not_found_note")
        content = f"❌ **{title}**\n\n{description}\n{note}"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class BlacklistAddSuccessView(discord.ui.LayoutView):
    """View for blacklist add success"""

    def __init__(
        self, server_name: str, server_id: str, translator, reason: str = None
    ):
        super().__init__()

        title = translator.get("commands.admin.blacklist.add.success_title")
        description = translator.get(
            "commands.admin.blacklist.add.success_description",
            server_name=server_name,
            server_id=server_id,
        )
        default_reason = translator.get("commands.admin.blacklist.no_reason_provided")
        reason_text = translator.get(
            "commands.admin.blacklist.add.success_reason",
            reason=reason or default_reason,
        )
        note1 = translator.get("commands.admin.blacklist.add.success_note_1")
        note2 = translator.get("commands.admin.blacklist.add.success_note_2")

        content = (
            f"✅ **{title}**\n\n"
            f"{description}\n\n"
            f"📝 **{reason_text}**\n\n"
            f"{note1}\n"
            f"{note2}"
        )

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class BlacklistAddAlreadyView(discord.ui.LayoutView):
    """View for server already blacklisted"""

    def __init__(self, server_id: str, translator):
        super().__init__()

        title = translator.get("commands.admin.blacklist.add.already_title")
        description = translator.get(
            "commands.admin.blacklist.add.already_description", server_id=server_id
        )
        content = f"❌ **{title}**\n\n{description}"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class BlacklistRemoveSuccessView(discord.ui.LayoutView):
    """View for blacklist remove success"""

    def __init__(self, server_id: str, translator):
        super().__init__()

        title = translator.get("commands.admin.blacklist.remove.success_title")
        description = translator.get(
            "commands.admin.blacklist.remove.success_description", server_id=server_id
        )
        note = translator.get("commands.admin.blacklist.remove.success_note")
        content = f"✅ **{title}**\n\n{description}\n\n{note}"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class BlacklistRemoveNotFoundView(discord.ui.LayoutView):
    """View for server not blacklisted"""

    def __init__(self, server_id: str, translator):
        super().__init__()

        title = translator.get("commands.admin.blacklist.remove.not_found_title")
        description = translator.get(
            "commands.admin.blacklist.remove.not_found_description", server_id=server_id
        )
        content = f"❌ **{title}**\n\n{description}"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class BlacklistCheckNotFoundView(discord.ui.LayoutView):
    """View for when a server is not blacklisted"""

    def __init__(self, server_id: str, translator):
        super().__init__()

        title = translator.get("commands.admin.blacklist.check.not_blacklisted_title")
        description = translator.get(
            "commands.admin.blacklist.check.not_blacklisted_description",
            server_id=server_id,
        )
        note = translator.get("commands.admin.blacklist.check.not_blacklisted_note")
        content = f"✅ **{title}**\n\n{description}\n{note}"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class BlacklistCheckFoundView(discord.ui.LayoutView):
    """View for when a server is blacklisted"""

    def __init__(self, server_id: str, server_name: str, entry, translator):
        super().__init__()

        blacklisted_date = translator.get("commands.admin.blacklist.check.unknown_date")
        if entry.blacklisted_at:
            blacklisted_date = f"<t:{int(entry.blacklisted_at.timestamp())}:F>"

        title = translator.get("commands.admin.blacklist.check.blacklisted_title")
        server_name_label = translator.get(
            "commands.admin.blacklist.check.blacklisted_server_name"
        )
        server_id_label = translator.get(
            "commands.admin.blacklist.check.blacklisted_server_id"
        )
        reason_label = translator.get(
            "commands.admin.blacklist.check.blacklisted_reason"
        )
        default_reason = translator.get("commands.admin.blacklist.no_reason_provided")
        blacklisted_label = translator.get(
            "commands.admin.blacklist.check.blacklisted_date"
        )
        blacklisted_by_label = translator.get(
            "commands.admin.blacklist.check.blacklisted_by"
        )
        note = translator.get("commands.admin.blacklist.check.blacklisted_note")

        content = (
            f"🚫 **{title}**\n\n"
            f"**{server_name_label}:** {server_name}\n"
            f"**{server_id_label}:** `{server_id}`\n"
            f"**{reason_label}:** {entry.reason or default_reason}\n"
            f"**{blacklisted_label}:** {blacklisted_date}\n"
            f"**{blacklisted_by_label}:** <@{entry.blacklisted_by}>\n\n"
            f"{note}"
        )

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class ErrorNotFoundView(discord.ui.LayoutView):
    """View for error not found"""

    def __init__(self, error_id: str, translator):
        super().__init__()

        title = translator.get("commands.admin.error.check.not_found_title")
        description = translator.get(
            "commands.admin.error.check.not_found_description", error_id=error_id
        )
        content = f"❌ **{title}**\n\n{description}"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class ErrorDetailsView(discord.ui.LayoutView):
    """View for error details"""

    def __init__(self, error_doc, bot, translator):
        super().__init__()

        timestamp = int(error_doc.timestamp.timestamp())

        title = translator.get(
            "commands.admin.error.check.details_title", error_id=error_doc.error_id
        )
        level_label = translator.get("commands.admin.error.check.level")
        area_label = translator.get("commands.admin.error.check.area")
        time_label = translator.get("commands.admin.error.check.time")
        message_label = translator.get("commands.admin.error.check.message")
        server_label = translator.get("commands.admin.error.check.server")
        channel_label = translator.get("commands.admin.error.check.channel")
        user_label = translator.get("commands.admin.error.check.user")
        command_label = translator.get("commands.admin.error.check.command")
        traceback_label = translator.get("commands.admin.error.check.traceback")
        no_message = translator.get("commands.admin.error.check.no_message")
        unknown_text = translator.get("commands.admin.error.check.unknown")

        content = f"**{title}**\n\n"
        content += f"**{level_label}:** {error_doc.level}\n"
        content += f"**{area_label}:** {error_doc.area}\n"
        content += f"**{time_label}:** <t:{timestamp}:F>\n\n"

        message = error_doc.message or no_message
        if len(message) > 500:
            message = message[:497] + "..."
        content += f"**{message_label}:** {message}\n\n"

        if error_doc.guild_id:
            guild = bot.get_guild(int(error_doc.guild_id))
            guild_name = guild.name if guild else unknown_text
            content += f"**{server_label}:** {guild_name} ({error_doc.guild_id})\n"

        if error_doc.channel_id:
            channel = bot.get_channel(int(error_doc.channel_id))
            channel_name = channel.name if channel else unknown_text
            content += f"**{channel_label}:** {channel_name} ({error_doc.channel_id})\n"

        if error_doc.user_id:
            content += (
                f"**{user_label}:** <@{error_doc.user_id}> ({error_doc.user_id})\n"
            )

        if error_doc.command:
            content += f"**{command_label}:** {error_doc.command}\n"

        if error_doc.stack_trace:
            tb = error_doc.stack_trace
            if len(tb) > 800:
                tb = tb[:797] + "..."
            content += f"\n**{traceback_label}:**\n```python\n{tb}\n```"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class ErrorDeleteSuccessView(discord.ui.LayoutView):
    """View for error delete success"""

    def __init__(self, error_id: str, translator):
        super().__init__()

        title = translator.get("commands.admin.error.delete_success_title")
        description = translator.get(
            "commands.admin.error.delete_success_description", error_id=error_id
        )
        content = f"✅ **{title}**\n\n{description}"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class ErrorDeleteFailedView(discord.ui.LayoutView):
    """View for error delete failed"""

    def __init__(self, error_id: str, translator):
        super().__init__()

        title = translator.get("commands.admin.error.delete_failed_title")
        description = translator.get(
            "commands.admin.error.delete_failed_description", error_id=error_id
        )
        note = translator.get("commands.admin.error.delete_failed_note")
        content = f"❌ **{title}**\n\n{description}\n{note}"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class NoErrorsView(discord.ui.LayoutView):
    """View for no errors found"""

    def __init__(self, translator):
        super().__init__()

        title = translator.get("commands.admin.error.no_errors_title")
        description = translator.get("commands.admin.error.no_errors_description")
        content = f"ℹ️ **{title}**\n\n{description}"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.greyple().value,
        )
        self.add_item(container)


class ErrorListView(discord.ui.LayoutView):
    """View for error list"""

    def __init__(self, errors: list, translator):
        super().__init__()

        title = translator.get("commands.admin.error.list_title")
        last_text = translator.get('commands.admin.error.list_last', count=len(errors))
        content = f"**{title}** ({last_text})\n\n"

        id_label = translator.get("commands.admin.error.list_item_id")
        level_label = translator.get("commands.admin.error.list_item_level")
        area_label = translator.get("commands.admin.error.list_item_area")
        time_label = translator.get("commands.admin.error.list_item_time")
        message_label = translator.get("commands.admin.error.list_item_message")

        for error in errors[:10]:  # Show first 10
            timestamp = f"<t:{int(error.timestamp.timestamp())}:R>"
            message = error.message
            if len(message) > 50:
                message = message[:47] + "..."

            content += (
                f"**{id_label}:** `{error.error_id}` | **{level_label}:** {error.level}\n"
                f"**{area_label}:** {error.area}\n"
                f"**{time_label}:** {timestamp}\n"
                f"**{message_label}:** {message}\n"
                f"---\n"
            )

        if len(errors) > 10:
            more_text = translator.get(
                "commands.admin.error.list_more", count=len(errors) - 10
            )
            content += f"\n{more_text}\n"

        hint = translator.get("commands.admin.error.list_hint")
        content += f"\n_{hint}_"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.yellow().value,
        )
        self.add_item(container)


class ErrorsClearedView(discord.ui.LayoutView):
    """View for errors cleared"""

    def __init__(self, count: int, translator):
        super().__init__()

        title = translator.get("commands.admin.error.clear_success_title")
        description = translator.get(
            "commands.admin.error.clear_success_description",
            count=count,
            s="" if count == 1 else "s"
        )
        note = translator.get("commands.admin.error.clear_success_note")
        content = f"✅ **{title}**\n\n{description}\n\n_{note}_"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class ErrorsClearFailedView(discord.ui.LayoutView):
    """View for errors clear failed"""

    def __init__(self, error_id: str, translator):
        super().__init__()

        title = translator.get("commands.admin.error.clear_failed_title")
        description = translator.get("commands.admin.error.clear_failed_description")
        error_text = translator.get(
            "commands.admin.error.clear_failed_error_id", error_id=error_id
        )
        note = translator.get("commands.admin.error.clear_failed_note")
        content = f"❌ **{title}**\n\n{description}\n\n{error_text}\n\n_{note}_"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class ForceUnsubNotFoundView(discord.ui.LayoutView):
    """View for force unsubscribe not found"""

    def __init__(self, target_id: str, translator):
        super().__init__()

        title = translator.get("commands.admin.force.not_found_title")
        description = translator.get(
            "commands.admin.force.not_found_description", target_id=target_id
        )
        note = translator.get("commands.admin.force.not_found_note")
        content = f"❌ **{title}**\n\n{description}\n\n_{note}_"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class ForceUnsubSuccessView(discord.ui.LayoutView):
    """View for force unsubscribe success"""

    def __init__(
        self,
        target_type: str,
        target_id: str,
        translator,
        count: int = None,
        server_id: str = None,
    ):
        super().__init__()

        if target_type == "server":
            title = translator.get("commands.admin.force.server_success_title")
            description = translator.get(
                "commands.admin.force.server_success_description",
                count=count,
                s="" if count == 1 else "s",
                server_id=target_id,
            )
            note = translator.get("commands.admin.force.server_success_note")
            content = f"✅ **{title}**\n\n{description}\n\n_{note}_"
        else:  # channel
            title = translator.get("commands.admin.force.channel_success_title")
            description = translator.get(
                "commands.admin.force.channel_success_description",
                channel_id=target_id,
                server_id=server_id,
            )
            note = translator.get("commands.admin.force.channel_success_note")
            content = f"✅ **{title}**\n\n{description}\n\n_{note}_"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class RecacheSuccessView(discord.ui.LayoutView):
    """View for successful recache operation"""

    def __init__(
        self,
        cache_type: str,
        translator,
        servers: int = 0,
        blacklist: int = 0,
        channels: int = 0,
        timezones: int = 0,
    ):
        super().__init__()

        title = translator.get("commands.admin.recache.success_title")
        description = translator.get(
            "commands.admin.recache.success_description", cache_type=cache_type
        )
        content = f"✅ **{title}**\n\n{description}\n\n"

        if servers > 0 or blacklist > 0 or channels > 0 or timezones > 0:
            loaded_data = translator.get("commands.admin.recache.success_loaded_data")
            content += f"**📊 {loaded_data}**\n"
            if servers > 0:
                content += (
                    translator.get(
                        "commands.admin.recache.success_servers", count=servers
                    )
                    + "\n"
                )
            if channels > 0:
                content += (
                    translator.get(
                        "commands.admin.recache.success_channels", count=channels
                    )
                    + "\n"
                )
            if blacklist > 0:
                content += (
                    translator.get(
                        "commands.admin.recache.success_blacklist", count=blacklist
                    )
                    + "\n"
                )
            if timezones > 0:
                content += (
                    translator.get(
                        "commands.admin.recache.success_timezones", count=timezones
                    )
                    + "\n"
                )

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class RecacheErrorView(discord.ui.LayoutView):
    """View for recache error"""

    def __init__(self, cache_type: str, error: str, translator):
        super().__init__()

        title = translator.get("commands.admin.recache.error_title")
        description = translator.get(
            "commands.admin.recache.error_description", cache_type=cache_type
        )
        error_msg = translator.get("commands.admin.recache.error_message", error=error)
        content = f"❌ **{title}**\n\n{description}\n\n{error_msg}"

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)
