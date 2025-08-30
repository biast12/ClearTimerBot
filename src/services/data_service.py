import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Set
from contextlib import asynccontextmanager

from src.models import Server


class DataService:
    def __init__(
        self,
        servers_file: Path = Path('servers.json'),
        blacklist_file: Path = Path('blacklist.json'),
        timezones_file: Path = Path('timezones.json')
    ):
        self.servers_file = servers_file
        self.blacklist_file = blacklist_file
        self.timezones_file = timezones_file
        self._lock = asyncio.Lock()
        self._servers: Dict[str, Server] = {}
        self._blacklist: Set[str] = set()
        self._timezones: Dict[str, str] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        if self._initialized:
            return
        
        async with self._lock:
            self._servers = await self._load_servers()
            self._blacklist = await self._load_blacklist()
            self._timezones = await self._load_timezones()
            self._initialized = True
    
    async def _load_servers(self) -> Dict[str, Server]:
        if not self.servers_file.exists():
            return {}
        
        try:
            with open(self.servers_file, 'r') as f:
                data = json.load(f)
            
            servers = {}
            for server_id, server_data in data.items():
                servers[server_id] = Server.from_dict(server_id, server_data)
            return servers
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading servers: {e}")
            return {}
    
    async def _load_blacklist(self) -> Set[str]:
        if not self.blacklist_file.exists():
            return set()
        
        try:
            with open(self.blacklist_file, 'r') as f:
                data = json.load(f)
            return set(data) if isinstance(data, list) else set()
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error loading blacklist: {e}")
            return set()
    
    async def _load_timezones(self) -> Dict[str, str]:
        if not self.timezones_file.exists():
            return {}
        
        try:
            with open(self.timezones_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error loading timezones: {e}")
            return {}
    
    async def save_servers(self) -> None:
        async with self._lock:
            data = {
                server_id: server.to_dict()
                for server_id, server in self._servers.items()
            }
            
            with open(self.servers_file, 'w') as f:
                json.dump(data, f, indent=4)
    
    async def save_blacklist(self) -> None:
        async with self._lock:
            with open(self.blacklist_file, 'w') as f:
                json.dump(list(self._blacklist), f, indent=4)
    
    async def get_server(self, server_id: str) -> Optional[Server]:
        async with self._lock:
            return self._servers.get(server_id)
    
    async def add_server(self, server_id: str, server_name: str) -> Server:
        async with self._lock:
            if server_id not in self._servers:
                self._servers[server_id] = Server(server_id, server_name)
            return self._servers[server_id]
    
    async def remove_server(self, server_id: str) -> bool:
        async with self._lock:
            if server_id in self._servers:
                del self._servers[server_id]
                return True
            return False
    
    async def get_all_servers(self) -> Dict[str, Server]:
        async with self._lock:
            return self._servers.copy()
    
    async def is_blacklisted(self, server_id: str) -> bool:
        async with self._lock:
            return server_id in self._blacklist
    
    async def add_to_blacklist(self, server_id: str) -> bool:
        async with self._lock:
            if server_id not in self._blacklist:
                self._blacklist.add(server_id)
                return True
            return False
    
    async def remove_from_blacklist(self, server_id: str) -> bool:
        async with self._lock:
            if server_id in self._blacklist:
                self._blacklist.remove(server_id)
                return True
            return False
    
    async def get_blacklist(self) -> List[str]:
        async with self._lock:
            return list(self._blacklist)
    
    def get_timezone(self, timezone_abbr: str) -> Optional[str]:
        return self._timezones.get(timezone_abbr)
    
    @asynccontextmanager
    async def transaction(self):
        async with self._lock:
            backup_servers = self._servers.copy()
            backup_blacklist = self._blacklist.copy()
            
            try:
                yield self
                await self.save_servers()
                await self.save_blacklist()
            except Exception:
                self._servers = backup_servers
                self._blacklist = backup_blacklist
                raise