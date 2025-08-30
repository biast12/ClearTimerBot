from typing import Dict, List, Optional, Set, Any
import asyncio
from datetime import datetime, timezone, timedelta

from src.models import Server
from src.services.database import db_manager
from src.services.cache_manager import MultiLevelCache


class DataService:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._servers_cache: Dict[str, Server] = {}
        self._blacklist_cache: Set[str] = set()
        self._timezones_cache: Dict[str, str] = {}
        self._cache = MultiLevelCache()
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
        # Check memory cache first
        cache_key = f"server:{server_id}"
        cached_server = await self._cache.get(cache_key)
        if cached_server is not None:
            return cached_server

        async with self._lock:
            if server_id in self._servers_cache:
                server = self._servers_cache[server_id]
                await self._cache.set(cache_key, server, cache_level="memory")
                return server

            servers_collection = db_manager.servers
            server_doc = await servers_collection.find_one({"_id": server_id})
            if server_doc:
                server = Server.from_dict(server_id, server_doc)
                self._servers_cache[server_id] = server
                await self._cache.set(cache_key, server, cache_level="warm")
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
                
                # Invalidate cache for this server
                cache_key = f"server:{server_id}"
                await self._cache.invalidate(cache_key)
            return self._servers_cache[server_id]

    async def remove_server(self, server_id: str) -> bool:
        async with self._lock:
            if server_id in self._servers_cache:
                del self._servers_cache[server_id]

                servers_collection = db_manager.servers
                result = await servers_collection.delete_one({"_id": server_id})
                
                # Invalidate cache for this server
                cache_key = f"server:{server_id}"
                await self._cache.invalidate(cache_key)
                
                return result.deleted_count > 0
            return False

    async def get_all_servers(self) -> Dict[str, Server]:
        async with self._lock:
            return self._servers_cache.copy()

    async def is_blacklisted(self, server_id: str) -> bool:
        # Check cache first
        cache_key = f"blacklist:{server_id}"
        cached_result = await self._cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        async with self._lock:
            result = server_id in self._blacklist_cache
            await self._cache.set(cache_key, result, cache_level="warm", ttl=600)  # 10 minutes
            return result

    async def add_to_blacklist(self, server_id: str) -> bool:
        async with self._lock:
            if server_id not in self._blacklist_cache:
                self._blacklist_cache.add(server_id)

                # Update the blacklist document
                blacklist_collection = db_manager.blacklist
                await blacklist_collection.update_one(
                    {}, {"$addToSet": {"blacklist": server_id}}, upsert=True
                )
                
                # Invalidate cache
                cache_key = f"blacklist:{server_id}"
                await self._cache.invalidate(cache_key)
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
                
                # Invalidate cache
                cache_key = f"blacklist:{server_id}"
                await self._cache.invalidate(cache_key)
                return True
            return False

    async def get_blacklist(self) -> List[str]:
        async with self._lock:
            return list(self._blacklist_cache)

    def get_timezone(self, timezone_abbr: str) -> Optional[str]:
        return self._timezones_cache.get(timezone_abbr)
    
    async def get_removed_server(self, server_id: str) -> Optional[Dict]:
        cache_key = f"removed_server:{server_id}"
        cached_doc = await self._cache.get(cache_key)
        if cached_doc is not None:
            return cached_doc
        
        removed_servers_collection = db_manager.removed_servers
        doc = await removed_servers_collection.find_one({"_id": server_id})
        if doc:
            await self._cache.set(cache_key, doc, cache_level="cold", ttl=1800)  # 30 minutes
        return doc
    
    async def cache_removed_server(self, server_id: str, server_doc: Dict) -> None:
        cache_key = f"removed_server:{server_id}"
        await self._cache.set(cache_key, server_doc, cache_level="cold", ttl=1800)
    
    async def invalidate_removed_server_cache(self, server_id: str) -> None:
        cache_key = f"removed_server:{server_id}"
        await self._cache.invalidate(cache_key)
    
    def get_cache_stats(self) -> Dict:
        return self._cache.get_all_stats()

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
