from dataclasses import dataclass
from datetime import datetime, timezone
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
            "locale": self.locale,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GuildInfo":
        joined_at = data.get("joined_at")
        if isinstance(joined_at, str):
            joined_at = datetime.fromisoformat(joined_at)
        elif joined_at is None:
            joined_at = datetime.now(timezone.utc)

        if joined_at.tzinfo is None:
            joined_at = joined_at.replace(tzinfo=timezone.utc)

        return cls(
            guild_id=str(data["guild_id"]),
            guild_name=data.get("guild_name", "Unknown"),
            member_count=data.get("member_count", 0),
            owner_id=str(data.get("owner_id", "")),
            joined_at=joined_at,
            premium_tier=data.get("premium_tier", 0),
            locale=data.get("locale"),
        )
