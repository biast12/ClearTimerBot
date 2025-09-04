from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


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