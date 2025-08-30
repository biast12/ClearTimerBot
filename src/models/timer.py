from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class ChannelTimer:
    channel_id: str
    timer: str
    next_run_time: datetime
    
    def to_dict(self) -> Dict:
        return {
            'timer': self.timer,
            'next_run_time': self.next_run_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, channel_id: str, data: Dict) -> 'ChannelTimer':
        return cls(
            channel_id=channel_id,
            timer=data['timer'],
            next_run_time=datetime.fromisoformat(data['next_run_time'])
        )


@dataclass
class Server:
    server_id: str
    server_name: str
    channels: Dict[str, ChannelTimer] = field(default_factory=dict)
    
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
            'server_name': self.server_name,
            'channels': {
                channel_id: timer.to_dict()
                for channel_id, timer in self.channels.items()
            }
        }
    
    @classmethod
    def from_dict(cls, server_id: str, data: Dict) -> 'Server':
        server = cls(
            server_id=server_id,
            server_name=data['server_name']
        )
        for channel_id, channel_data in data.get('channels', {}).items():
            server.channels[channel_id] = ChannelTimer.from_dict(channel_id, channel_data)
        return server