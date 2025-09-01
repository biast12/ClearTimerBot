"""
Utility functions for parsing and validating ignore targets (messages and users)
"""

import re
import discord
from typing import Optional, Tuple


async def identify_and_validate_ignore_target(
    target: str,
    channel: discord.TextChannel,
    guild: discord.Guild
) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse and validate a target string to determine if it's a user or message.
    
    Args:
        target: The target string (message ID/link or user mention/ID)
        channel: The channel to check for messages
        guild: The guild to check for users
    
    Returns:
        Tuple of (entity_id, entity_type) where entity_type is 'user' or 'message'
        Returns (None, None) if target is invalid
    """
    # First try to parse as user
    user_id = extract_discord_user_id(target)
    if user_id:
        # Validate user exists in guild
        try:
            member = await guild.fetch_member(int(user_id))
            if member:
                return user_id, "user"
        except (discord.NotFound, discord.HTTPException, ValueError):
            pass  # Not a valid user, try message next
    
    # Try to parse as message
    message_id = extract_discord_message_id(target)
    if message_id:
        # Try to validate message exists in channel
        try:
            message = await channel.fetch_message(int(message_id))
            if message:
                return message_id, "message"
        except (discord.NotFound, discord.HTTPException, ValueError):
            # Message might be in a different channel or deleted
            # Still return it as valid since user explicitly provided it
            return message_id, "message"
    
    return None, None


def extract_discord_user_id(user_input: str) -> Optional[str]:
    """
    Extract user ID from mention or direct ID.
    
    Args:
        user_input: String containing user mention or ID
    
    Returns:
        User ID string or None if not a valid user reference
    """
    # Check if it's a user mention <@123456789> or <@!123456789>
    mention_pattern = r"<@!?(\d+)>"
    match = re.match(mention_pattern, user_input)
    if match:
        return match.group(1)
    
    # Check if it's a direct user ID (digits only, typically 17-20 digits)
    if user_input.isdigit() and 17 <= len(user_input) <= 20:
        return user_input
    
    return None


def extract_discord_message_id(message_input: str) -> Optional[str]:
    """
    Extract message ID from either a message link or direct ID.
    
    Args:
        message_input: String containing message link or ID
    
    Returns:
        Message ID string or None if not a valid message reference
    """
    # Check if it's a message link
    link_pattern = r"https://discord(?:app)?\.com/channels/\d+/\d+/(\d+)"
    match = re.match(link_pattern, message_input)
    if match:
        return match.group(1)
    
    # Check if it's a direct message ID (digits only, typically 17+ digits)
    # Messages IDs are typically longer and we check length to distinguish from user IDs
    if message_input.isdigit() and len(message_input) >= 17:
        # If it could be either user or message, we'll let the validation step determine
        return message_input
    
    return None


async def validate_and_add_ignore_target(
    target: Optional[str],
    channel: discord.TextChannel,
    guild: discord.Guild,
    channel_timer
) -> Tuple[Optional[str], Optional[str]]:
    """
    Validate and add a target to the channel timer's ignore list.
    
    Args:
        target: The target string to parse and add
        channel: The channel for message validation
        guild: The guild for user validation
        channel_timer: The channel timer object to add the target to
    
    Returns:
        Tuple of (entity_id, entity_type) if successfully added, (None, None) otherwise
    """
    if not target:
        return None, None
    
    entity_id, entity_type = await identify_and_validate_ignore_target(target, channel, guild)
    
    if entity_id and entity_type:
        if entity_type == "user":
            # Check if not already ignored
            if entity_id not in channel_timer.ignored.users:
                channel_timer.add_ignored_user(entity_id)
                return entity_id, entity_type
        else:  # message
            # Check if not already ignored
            if entity_id not in channel_timer.ignored.messages:
                channel_timer.add_ignored_message(entity_id)
                return entity_id, entity_type
    
    return None, None