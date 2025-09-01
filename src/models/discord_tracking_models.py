from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class PermissionLevel(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"


class CommandCategory(Enum):
    SUBSCRIPTION = "subscription"
    INFORMATION = "information"
    UTILITY = "utility"
    OWNER = "owner"
    MODERATION = "moderation"


@dataclass
class CommandUsage:
    command_name: str
    user_id: str
    guild_id: Optional[str]
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command_name": self.command_name,
            "user_id": self.user_id,
            "guild_id": self.guild_id,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error_message": self.error_message
        }


@dataclass
class GuildInfo:
    guild_id: str
    guild_name: str
    member_count: int
    owner_id: str
    joined_at: datetime
    premium_tier: int = 0
    locale: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "guild_id": self.guild_id,
            "guild_name": self.guild_name,
            "member_count": self.member_count,
            "owner_id": self.owner_id,
            "joined_at": self.joined_at.isoformat(),
            "premium_tier": self.premium_tier,
            "locale": self.locale
        }


@dataclass
class ChannelInfo:
    channel_id: str
    channel_name: str
    guild_id: str
    channel_type: str
    category_id: Optional[str] = None
    position: int = 0
    nsfw: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel_id": self.channel_id,
            "channel_name": self.channel_name,
            "guild_id": self.guild_id,
            "channel_type": self.channel_type,
            "category_id": self.category_id,
            "position": self.position,
            "nsfw": self.nsfw
        }


@dataclass
class UserInfo:
    user_id: str
    username: str
    discriminator: str
    avatar_hash: Optional[str] = None
    bot: bool = False
    system: bool = False
    
    @property
    def full_username(self) -> str:
        return f"{self.username}#{self.discriminator}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "discriminator": self.discriminator,
            "full_username": self.full_username,
            "avatar_hash": self.avatar_hash,
            "bot": self.bot,
            "system": self.system
        }


@dataclass
class MessageInfo:
    message_id: str
    channel_id: str
    guild_id: Optional[str]
    author_id: str
    content: str
    timestamp: datetime
    edited_at: Optional[datetime] = None
    pinned: bool = False
    mentions: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    embeds: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "channel_id": self.channel_id,
            "guild_id": self.guild_id,
            "author_id": self.author_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "pinned": self.pinned,
            "mentions": self.mentions,
            "attachments": self.attachments,
            "embeds": self.embeds
        }


@dataclass
class EmbedField:
    name: str
    value: str
    inline: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "inline": self.inline
        }


@dataclass
class EmbedData:
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    color: Optional[int] = None
    fields: List[EmbedField] = field(default_factory=list)
    footer_text: Optional[str] = None
    footer_icon_url: Optional[str] = None
    author_name: Optional[str] = None
    author_url: Optional[str] = None
    author_icon_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    image_url: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def add_field(self, name: str, value: str, inline: bool = False) -> None:
        self.fields.append(EmbedField(name, value, inline))
    
    def to_dict(self) -> Dict[str, Any]:
        data = {}
        if self.title:
            data["title"] = self.title
        if self.description:
            data["description"] = self.description
        if self.url:
            data["url"] = self.url
        if self.color is not None:
            data["color"] = self.color
        if self.fields:
            data["fields"] = [field.to_dict() for field in self.fields]
        if self.footer_text or self.footer_icon_url:
            data["footer"] = {}
            if self.footer_text:
                data["footer"]["text"] = self.footer_text
            if self.footer_icon_url:
                data["footer"]["icon_url"] = self.footer_icon_url
        if self.author_name or self.author_url or self.author_icon_url:
            data["author"] = {}
            if self.author_name:
                data["author"]["name"] = self.author_name
            if self.author_url:
                data["author"]["url"] = self.author_url
            if self.author_icon_url:
                data["author"]["icon_url"] = self.author_icon_url
        if self.thumbnail_url:
            data["thumbnail"] = {"url": self.thumbnail_url}
        if self.image_url:
            data["image"] = {"url": self.image_url}
        if self.timestamp:
            data["timestamp"] = self.timestamp.isoformat()
        return data