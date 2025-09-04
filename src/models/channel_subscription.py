from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, List


@dataclass
class IgnoredEntities:
    """Container for ignored messages and users"""
    messages: List[str] = field(default_factory=list)
    users: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "messages": self.messages,
            "users": self.users
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "IgnoredEntities":
        return cls(
            messages=data.get("messages", []),
            users=data.get("users", [])
        )


@dataclass
class ChannelTimer:
    channel_id: str
    timer: str
    next_run_time: datetime
    ignored: IgnoredEntities = field(default_factory=IgnoredEntities)
    view_message_id: Optional[str] = None
    # Keep backward compatibility
    _legacy_ignored_messages: Optional[List[str]] = field(default=None, init=False)

    def to_dict(self) -> Dict:
        data = {
            "timer": self.timer, 
            "next_run_time": self.next_run_time.isoformat(),
            "ignored": self.ignored.to_dict()
        }
        if self.view_message_id:
            data["view_message_id"] = self.view_message_id
        return data

    @classmethod
    def from_dict(cls, channel_id: str, data: Dict) -> "ChannelTimer":
        # Handle backward compatibility
        if "ignored" in data:
            ignored = IgnoredEntities.from_dict(data["ignored"])
        elif "ignored_messages" in data:
            # Migrate old format
            ignored = IgnoredEntities(messages=data.get("ignored_messages", []))
        else:
            ignored = IgnoredEntities()
        
        return cls(
            channel_id=channel_id,
            timer=data["timer"],
            next_run_time=datetime.fromisoformat(data["next_run_time"]),
            ignored=ignored,
            view_message_id=data.get("view_message_id")
        )
    
    # Backward compatibility properties
    @property
    def ignored_messages(self) -> List[str]:
        return self.ignored.messages
    
    def add_ignored_message(self, message_id: str) -> bool:
        if message_id not in self.ignored.messages:
            self.ignored.messages.append(message_id)
            return True
        return False
    
    def remove_ignored_message(self, message_id: str) -> bool:
        if message_id in self.ignored.messages:
            self.ignored.messages.remove(message_id)
            return True
        return False
    
    def add_ignored_user(self, user_id: str) -> bool:
        if user_id not in self.ignored.users:
            self.ignored.users.append(user_id)
            return True
        return False
    
    def remove_ignored_user(self, user_id: str) -> bool:
        if user_id in self.ignored.users:
            self.ignored.users.remove(user_id)
            return True
        return False


@dataclass
class Server:
    server_id: str
    server_name: str
    channels: Dict[str, ChannelTimer] = field(default_factory=dict)
    timezone: Optional[str] = None
    timezone_auto_detected: bool = False

    def add_channel(self, channel_id: str, timer: str, next_run_time: datetime) -> None:
        self.channels[channel_id] = ChannelTimer(channel_id, timer, next_run_time)

    def remove_channel(self, channel_id: str) -> bool:
        if channel_id in self.channels:
            del self.channels[channel_id]
            return True
        return False

    def get_channel(self, channel_id: str) -> Optional[ChannelTimer]:
        return self.channels.get(channel_id)

    def to_dict(self) -> Dict:
        return {
            "server_name": self.server_name or "",
            "channels": {
                channel_id: timer.to_dict()
                for channel_id, timer in self.channels.items()
            },
            "timezone": self.timezone,
            "timezone_auto_detected": self.timezone_auto_detected,
        }

    @classmethod
    def from_dict(cls, server_id: str, data: Dict) -> "Server":
        server = cls(
            server_id=server_id,
            server_name=data.get("server_name", "") or "",
            timezone=data.get("timezone"),
            timezone_auto_detected=data.get("timezone_auto_detected", False)
        )
        for channel_id, channel_data in data.get("channels", {}).items():
            server.channels[channel_id] = ChannelTimer.from_dict(
                channel_id, channel_data
            )
        return server
