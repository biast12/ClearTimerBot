"""
View components for subscription commands with full localization
"""

import discord
from typing import Optional, List, Tuple
from datetime import datetime
from src.utils.footer import add_footer


class SubscriptionSuccessView(discord.ui.LayoutView):
    """View for subscription success message"""

    def __init__(
        self,
        channel: discord.TextChannel,
        timer: str,
        next_run_time: datetime,
        translator,
        ignored_entity_id: Optional[str] = None,
        ignored_entity_type: Optional[str] = None,
    ):
        super().__init__()

        timestamp = int(next_run_time.timestamp())

        lines = []
        lines.append(
            translator.get(
                "commands.subscription.add.success",
                channel=channel.mention,
                timer=timer,
            )
        )
        lines.append("")
        lines.append(
            translator.get(
                "commands.subscription.info.next_clear",
                time=f"<t:{timestamp}:f> (<t:{timestamp}:R>)",
            )
        )

        if ignored_entity_id and ignored_entity_type:
            if ignored_entity_type == "user":
                lines.append("")
                lines.append(
                    translator.get(
                        "commands.subscription.info.ignored_users",
                        count=f"<@{ignored_entity_id}>",
                    )
                )
            else:
                lines.append("")
                lines.append(
                    translator.get(
                        "commands.subscription.info.ignored_messages",
                        count=f"`{ignored_entity_id}`",
                    )
                )

        content = add_footer("\n".join(lines), translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class InvalidTimerView(discord.ui.LayoutView):
    """View for invalid timer error"""

    def __init__(self, error_message: str, translator):
        super().__init__()

        content = add_footer(
            translator.get("errors.invalid_timer", timer=error_message), translator
        )

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class UnsubscribeSuccessView(discord.ui.LayoutView):
    """View for unsubscribe success"""

    def __init__(self, channel: discord.TextChannel, translator):
        super().__init__()

        content = add_footer(
            translator.get(
                "commands.subscription.remove.success", channel=channel.mention
            ),
            translator,
        )

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class NoActiveSubscriptionsView(discord.ui.LayoutView):
    """View for no active subscriptions error"""

    def __init__(self, translator):
        super().__init__()

        lines = [
            translator.get("commands.subscription.list.title"),
            "",
            translator.get("commands.subscription.list.no_subscriptions"),
        ]

        content = add_footer("\n".join(lines), translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class SubscriptionListView(discord.ui.LayoutView):
    """View for listing all active subscriptions in a server"""

    def __init__(
        self, guild: discord.Guild, channels: dict, scheduler_service, translator
    ):
        super().__init__()

        title = translator.get('commands.subscription.list.title')
        lines = [f"**{title}**", ""]

        if not channels:
            lines.append(translator.get("commands.subscription.list.no_subscriptions"))
        else:
            for channel_id, timer_info in channels.items():
                channel = guild.get_channel(int(channel_id))
                if channel:
                    # Get next run time from scheduler
                    next_run_time = scheduler_service.get_channel_next_clear_time(
                        str(guild.id), channel_id
                    )

                    if next_run_time:
                        timestamp = int(next_run_time.timestamp())
                        next_clear = f"<t:{timestamp}:R>"
                    else:
                        next_clear = translator.get("common.unknown")

                    # Count ignored entities
                    ignored_count = 0
                    if hasattr(timer_info, "ignored"):
                        ignored_count = len(timer_info.ignored.messages) + len(
                            timer_info.ignored.users
                        )

                    if ignored_count > 0:
                        lines.append(
                            translator.get(
                                "commands.subscription.list.subscription_item_with_ignored",
                                channel=channel.mention,
                                timer=timer_info.timer,
                                next_clear=next_clear,
                                ignored_count=ignored_count,
                            )
                        )
                    else:
                        lines.append(
                            translator.get(
                                "commands.subscription.list.subscription_item",
                                channel=channel.mention,
                                timer=timer_info.timer,
                                next_clear=next_clear,
                            )
                        )

            lines.append("")
            lines.append(translator.get("commands.subscription.list.tip"))

        content = add_footer("\n".join(lines), translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value,
        )
        self.add_item(container)


class ChannelNotSubscribedView(discord.ui.LayoutView):
    """View for channel not subscribed error"""

    def __init__(self, channel: discord.TextChannel, translator):
        super().__init__()

        content = add_footer(
            translator.get("validation.not_subscribed", channel=channel.mention),
            translator,
        )

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class SubscriptionInfoView(discord.ui.LayoutView):
    """View for detailed subscription information"""

    def __init__(
        self,
        channel: discord.TextChannel,
        next_run_time: datetime,
        timer_info,
        translator,
    ):
        super().__init__()

        info_title = translator.get('commands.subscription.info.title')
        lines = [f"**{info_title}**", ""]

        channel_label = translator.get('common.channel')
        lines.append(f"**{channel_label}:** {channel.mention}")

        if timer_info:
            timestamp = int(next_run_time.timestamp())
            lines.append(translator.get("commands.subscription.info.subscribed"))
            lines.append(
                translator.get(
                    "commands.subscription.info.timer", timer=timer_info.timer
                )
            )
            lines.append(
                translator.get(
                    "commands.subscription.info.next_clear",
                    time=f"<t:{timestamp}:f> (<t:{timestamp}:R>)",
                )
            )

            # Show ignored entities
            if hasattr(timer_info, "ignored"):
                if timer_info.ignored.messages:
                    lines.append(
                        translator.get(
                            "commands.subscription.info.ignored_messages",
                            count=len(timer_info.ignored.messages),
                        )
                    )
                if timer_info.ignored.users:
                    lines.append(
                        translator.get(
                            "commands.subscription.info.ignored_users",
                            count=len(timer_info.ignored.users),
                        )
                    )
        else:
            lines.append(translator.get("validation.not_subscribed_status"))

        lines.append("")
        lines.append(translator.get("commands.subscription.info.commands_hint"))

        content = add_footer("\n".join(lines), translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value,
        )
        self.add_item(container)


class UpdateSuccessView(discord.ui.LayoutView):
    """View for successful timer update"""

    def __init__(
        self,
        channel: discord.TextChannel,
        timer: str,
        next_run_time: datetime,
        translator,
        ignored_entity_id: Optional[str] = None,
        ignored_entity_type: Optional[str] = None,
    ):
        super().__init__()

        timestamp = int(next_run_time.timestamp())

        lines = []
        lines.append(
            translator.get(
                "commands.subscription.update.success",
                channel=channel.mention,
                timer=timer,
            )
        )
        lines.append("")
        lines.append(
            translator.get(
                "commands.subscription.info.next_clear",
                time=f"<t:{timestamp}:f> (<t:{timestamp}:R>)",
            )
        )

        if ignored_entity_id and ignored_entity_type:
            lines.append("")
            if ignored_entity_type == "user":
                lines.append(
                    translator.get(
                        "commands.subscription.info.ignored_users",
                        count=f"<@{ignored_entity_id}>",
                    )
                )
            else:
                lines.append(
                    translator.get(
                        "commands.subscription.info.ignored_messages",
                        count=f"`{ignored_entity_id}`",
                    )
                )

        content = add_footer("\n".join(lines), translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class InvalidTargetView(discord.ui.LayoutView):
    """View for invalid target error"""

    def __init__(self, translator):
        super().__init__()

        content = add_footer(translator.get("errors.invalid_target"), translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class NoSubscriptionDataView(discord.ui.LayoutView):
    """View for no subscription data error"""

    def __init__(self, channel: discord.TextChannel, translator):
        super().__init__()

        content = add_footer(
            translator.get("components.no_data", channel=channel.mention), translator
        )

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class IgnoreEntityView(discord.ui.LayoutView):
    """View for ignore entity (message or user) add/remove"""

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        channel: discord.TextChannel,
        added: bool,
        translator,
    ):
        super().__init__()

        entity_name = entity_type.lower()

        if added:
            title_key = f'subscription.ignore.{entity_name}_added.title'
            desc_key = f'subscription.ignore.{entity_name}_added.description'
            title = translator.get(title_key)
            description = translator.get(desc_key, entity_id=entity_id, channel=channel.mention)
            content = add_footer(
                f"✅ **{title}**\n\n"
                f"{description}",
                translator
            )
        else:
            title_key = f'subscription.ignore.{entity_name}_removed.title'
            desc_key = f'subscription.ignore.{entity_name}_removed.description'
            title = translator.get(title_key)
            description = translator.get(desc_key, entity_id=entity_id, channel=channel.mention)
            content = add_footer(
                f"✅ **{title}**\n\n"
                f"{description}",
                translator
            )

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class ManualClearSuccessView(discord.ui.LayoutView):
    """View for manual clear success"""

    def __init__(self, deleted_count: int, channel: discord.TextChannel, translator):
        super().__init__()

        if deleted_count > 0:
            content = translator.get(
                "commands.subscription.clear.success", channel=channel.mention
            )
            messages_cleared = translator.get("commands.subscription.clear.messages_cleared")
            content += f"\n\n**{messages_cleared}:** {deleted_count}"
            color = discord.Color.green()
        else:
            content = translator.get(
                "commands.subscription.clear.no_messages", channel=channel.mention
            )
            color = discord.Color.blue()

        content = add_footer(content, translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content), accent_color=color.value
        )
        self.add_item(container)


class JobNotFoundView(discord.ui.LayoutView):
    """View for job not found error"""

    def __init__(self, channel: discord.TextChannel, translator):
        super().__init__()

        content = add_footer(
            translator.get("errors.job_not_found", channel=channel.mention), translator
        )

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class SkipSuccessView(discord.ui.LayoutView):
    """View for skip success"""

    def __init__(
        self, channel: discord.TextChannel, next_run_time: datetime, translator
    ):
        super().__init__()

        timestamp = int(next_run_time.timestamp())
        content = translator.get(
            "commands.subscription.skip.success",
            channel=channel.mention,
            next_clear=f"<t:{timestamp}:f> (<t:{timestamp}:R>)",
        )

        content = add_footer(content, translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class NextTimeNotFoundView(discord.ui.LayoutView):
    """View for next time not found error"""

    def __init__(self, channel: discord.TextChannel, translator):
        super().__init__()

        content = add_footer(
            translator.get("errors.next_time_not_found", channel=channel.mention),
            translator,
        )

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.red().value,
        )
        self.add_item(container)


class MultipleIgnoreEntityView(discord.ui.LayoutView):
    """View for multiple ignore entity toggle result"""

    def __init__(
        self,
        channel: discord.TextChannel,
        added_users: List[str],
        removed_users: List[str],
        added_messages: List[str],
        removed_messages: List[str],
        message_authors: dict,
        translator,
    ):
        super().__init__()

        lines = []

        if added_users:
            for user_id in added_users:
                lines.append(
                    translator.get(
                        "commands.subscription.ignore.user_added",
                        user=f"<@{user_id}>",
                        channel=channel.mention,
                    )
                )

        if removed_users:
            for user_id in removed_users:
                lines.append(
                    translator.get(
                        "commands.subscription.ignore.user_removed",
                        user=f"<@{user_id}>",
                        channel=channel.mention,
                    )
                )

        if added_messages:
            for msg_id in added_messages:
                author = message_authors.get(msg_id, translator.get("common.unknown"))
                lines.append(
                    translator.get(
                        "commands.subscription.ignore.message_added",
                        author=author,
                        channel=channel.mention,
                        message_id=msg_id,
                    )
                )

        if removed_messages:
            for msg_id in removed_messages:
                author = message_authors.get(msg_id, translator.get("common.unknown"))
                lines.append(
                    translator.get(
                        "commands.subscription.ignore.message_removed",
                        author=author,
                        channel=channel.mention,
                    )
                )

        content = add_footer("\n".join(lines), translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


# Views for multiple ignored entities
class SubscriptionSuccessWithMultipleIgnoresView(discord.ui.LayoutView):
    """View for subscription success with multiple ignored entities"""

    def __init__(
        self,
        channel: discord.TextChannel,
        timer: str,
        next_run_time: datetime,
        added_targets: List[Tuple[str, str]],
        translator,
    ):
        super().__init__()

        timestamp = int(next_run_time.timestamp())

        lines = []
        lines.append(
            translator.get(
                "commands.subscription.add.success_with_ignored",
                channel=channel.mention,
                timer=timer,
                count=len(added_targets),
            )
        )
        lines.append("")
        lines.append(
            translator.get(
                "commands.subscription.info.next_clear",
                time=f"<t:{timestamp}:f> (<t:{timestamp}:R>)",
            )
        )

        content = add_footer("\n".join(lines), translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


class UpdateSuccessWithMultipleIgnoresView(discord.ui.LayoutView):
    """View for update success with multiple ignored entities"""

    def __init__(
        self,
        channel: discord.TextChannel,
        timer: str,
        next_run_time: datetime,
        added_targets: List[Tuple[str, str]],
        translator,
    ):
        super().__init__()

        timestamp = int(next_run_time.timestamp())

        lines = []
        lines.append(
            translator.get(
                "commands.subscription.update.success_with_ignored",
                channel=channel.mention,
                timer=timer,
                count=len(added_targets),
            )
        )
        lines.append("")
        lines.append(
            translator.get(
                "commands.subscription.info.next_clear",
                time=f"<t:{timestamp}:f> (<t:{timestamp}:R>)",
            )
        )

        content = add_footer("\n".join(lines), translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.green().value,
        )
        self.add_item(container)


# Timer view message
class TimerViewMessage(discord.ui.LayoutView):
    """Persistent view message for timer display"""

    def __init__(
        self,
        channel: discord.TextChannel,
        timer: str,
        next_run_time: datetime,
        translator,
    ):
        super().__init__(timeout=None)  # Persistent view

        timestamp = int(next_run_time.timestamp())

        view_title = translator.get('subscription.timer_view.title', channel=channel.mention)
        timer_setting_label = translator.get('subscription.timer_view.timer_setting')
        next_clear_label = translator.get('subscription.timer_view.next_clear')
        time_remaining_label = translator.get('subscription.timer_view.time_remaining')
        auto_update_text = translator.get('subscription.timer_view.auto_update')
        
        content = (
            f"⏰ **{view_title}**\n\n"
            f"**{timer_setting_label}:** {timer}\n"
            f"**{next_clear_label}:** <t:{timestamp}:f>\n"
            f"**{time_remaining_label}:** <t:{timestamp}:R>\n\n"
            f"_{auto_update_text}_"
        )

        content = add_footer(content, translator)

        container = discord.ui.Container(
            discord.ui.TextDisplay(content=content),
            accent_color=discord.Color.blue().value,
        )
        self.add_item(container)
