from typing import Dict, List, Optional, Set
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timezone, timedelta

from src.models import Server
from src.services.database import db_manager


class DataService:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._servers_cache: Dict[str, Server] = {}
        self._blacklist_cache: Set[str] = set()
        self._timezones_cache: Dict[str, str] = {}
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return

        async with self._lock:
            await self._load_servers()
            await self._load_blacklist()
            await self._load_timezones()
            self._initialized = True

    async def _load_servers(self) -> None:
        servers_collection = db_manager.servers
        async for server_doc in servers_collection.find():
            server_id = str(server_doc["_id"])
            self._servers_cache[server_id] = Server.from_dict(server_id, server_doc)

    async def _load_blacklist(self) -> None:
        blacklist_collection = db_manager.blacklist
        blacklist_doc = await blacklist_collection.find_one()
        if blacklist_doc and "blacklist" in blacklist_doc:
            for server_id in blacklist_doc["blacklist"]:
                self._blacklist_cache.add(str(server_id))

    async def _load_timezones(self) -> None:
        timezones_collection = db_manager.timezones
        tz_doc = await timezones_collection.find_one()
        if tz_doc:
            for key, value in tz_doc.items():
                if key != "_id":
                    self._timezones_cache[key] = value

    async def save_servers(self) -> None:
        async with self._lock:
            servers_collection = db_manager.servers
            for server_id, server in self._servers_cache.items():
                server_data = server.to_dict()
                server_data["_id"] = server_id
                await servers_collection.replace_one(
                    {"_id": server_id}, server_data, upsert=True
                )

    async def save_blacklist(self) -> None:
        async with self._lock:
            blacklist_collection = db_manager.blacklist
            blacklist_data = {"blacklist": list(self._blacklist_cache)}

            # Replace the entire blacklist document
            await blacklist_collection.replace_one({}, blacklist_data, upsert=True)

    async def get_server(self, server_id: str) -> Optional[Server]:
        async with self._lock:
            if server_id in self._servers_cache:
                return self._servers_cache[server_id]

            servers_collection = db_manager.servers
            server_doc = await servers_collection.find_one({"_id": server_id})
            if server_doc:
                server = Server.from_dict(server_id, server_doc)
                self._servers_cache[server_id] = server
                return server
            return None

    async def add_server(self, server_id: str, server_name: str) -> Server:
        async with self._lock:
            if server_id not in self._servers_cache:
                server = Server(server_id, server_name)
                self._servers_cache[server_id] = server

                servers_collection = db_manager.servers
                server_data = server.to_dict()
                server_data["_id"] = server_id
                await servers_collection.insert_one(server_data)
            return self._servers_cache[server_id]

    async def remove_server(self, server_id: str) -> bool:
        async with self._lock:
            if server_id in self._servers_cache:
                del self._servers_cache[server_id]

                servers_collection = db_manager.servers
                result = await servers_collection.delete_one({"_id": server_id})
                return result.deleted_count > 0
            return False

    async def get_all_servers(self) -> Dict[str, Server]:
        async with self._lock:
            return self._servers_cache.copy()

    async def is_blacklisted(self, server_id: str) -> bool:
        async with self._lock:
            return server_id in self._blacklist_cache

    async def add_to_blacklist(self, server_id: str) -> bool:
        async with self._lock:
            if server_id not in self._blacklist_cache:
                self._blacklist_cache.add(server_id)

                # Update the blacklist document
                blacklist_collection = db_manager.blacklist
                await blacklist_collection.update_one(
                    {}, {"$addToSet": {"blacklist": server_id}}, upsert=True
                )
                return True
            return False

    async def remove_from_blacklist(self, server_id: str) -> bool:
        async with self._lock:
            if server_id in self._blacklist_cache:
                self._blacklist_cache.remove(server_id)

                # Update the blacklist document
                blacklist_collection = db_manager.blacklist
                await blacklist_collection.update_one(
                    {}, {"$pull": {"blacklist": server_id}}
                )
                return True
            return False

    async def get_blacklist(self) -> List[str]:
        async with self._lock:
            return list(self._blacklist_cache)

    def get_timezone(self, timezone_abbr: str) -> Optional[str]:
        return self._timezones_cache.get(timezone_abbr)

    async def refresh_cache(self) -> None:
        async with self._lock:
            self._servers_cache.clear()
            self._blacklist_cache.clear()
            self._timezones_cache.clear()

            await self._load_servers()
            await self._load_blacklist()
            await self._load_timezones()

    @asynccontextmanager
    async def transaction(self):
        async with self._lock:
            backup_servers = self._servers_cache.copy()
            backup_blacklist = self._blacklist_cache.copy()

            try:
                yield self
                await self.save_servers()
                await self.save_blacklist()
            except Exception:
                self._servers_cache = backup_servers
                self._blacklist_cache = backup_blacklist
                raise

    async def cleanup_old_removed_servers(self) -> int:
        """
        Remove servers from database that have been removed for more than 30 days.
        Returns the number of servers cleaned up.
        """
        removed_servers_collection = db_manager.removed_servers
        servers_collection = db_manager.servers

        # Calculate cutoff date (30 days ago)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

        # Find servers that were removed more than 30 days ago
        old_removed_servers = await removed_servers_collection.find(
            {"removed_at": {"$lt": cutoff_date}}
        ).to_list(None)

        cleaned_count = 0

        for server_doc in old_removed_servers:
            server_id = server_doc["_id"]
            server_name = server_doc.get("server_name", "Unknown")
            removed_at = server_doc.get("removed_at")

            # Remove from servers collection if it exists
            result = await servers_collection.delete_one({"_id": server_id})

            # Remove from cache if present
            if server_id in self._servers_cache:
                del self._servers_cache[server_id]

            # Remove from removed_servers collection
            await removed_servers_collection.delete_one({"_id": server_id})

            if result.deleted_count > 0:
                days_ago = (
                    (datetime.now(timezone.utc) - removed_at).days if removed_at else 30
                )
                print(
                    f"Cleaned up server: {server_name} (ID: {server_id}) - Removed {days_ago} days ago"
                )
                cleaned_count += 1

        if cleaned_count > 0:
            print(f"Total servers cleaned up: {cleaned_count}")

        return cleaned_count
