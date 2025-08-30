import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


@dataclass
class BotConfig:
    token: str
    owner_id: Optional[int] = None
    guild_id: Optional[int] = None
    
    @property
    def is_owner_mode(self) -> bool:
        return self.owner_id is not None and self.guild_id is not None


class ConfigManager:
    def __init__(self, env_path: Path = Path('.env')):
        self.env_path = env_path
        self._ensure_env_file()
        load_dotenv(self.env_path)
    
    def _ensure_env_file(self) -> None:
        if not self.env_path.exists():
            self.env_path.touch()
    
    def _get_or_prompt(self, key: str, prompt: str, required: bool = True) -> Optional[str]:
        value = os.getenv(key)
        if not value and (required or input(f"{prompt} (press Enter to skip): ").strip()):
            if not value:
                value = input(f"{prompt}: ").strip()
                if value:
                    self._save_to_env(key, value)
        return value if value else None
    
    def _save_to_env(self, key: str, value: str) -> None:
        with open(self.env_path, 'a') as f:
            f.write(f'{key}={value}\n')
        os.environ[key] = value
    
    def load_config(self) -> BotConfig:
        self._clear_console()
        
        token = self._get_or_prompt(
            'DISCORD_BOT_TOKEN',
            'Please enter your Discord bot token',
            required=True
        )
        
        if not token:
            raise ValueError("Bot token is required")
        
        owner_id_str = self._get_or_prompt(
            'OWNER_ID',
            'Please enter your User ID for owner commands',
            required=False
        )
        
        guild_id_str = self._get_or_prompt(
            'GUILD_ID',
            'Please enter your test server ID for owner commands',
            required=False
        )
        
        return BotConfig(
            token=token,
            owner_id=int(owner_id_str) if owner_id_str else None,
            guild_id=int(guild_id_str) if guild_id_str else None
        )
    
    @staticmethod
    def _clear_console() -> None:
        os.system('cls' if os.name == 'nt' else 'clear')