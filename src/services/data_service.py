from typing import Dict, List, Optional, Set, Any
import asyncio
from datetime import datetime, timezone, timedelta

from src.models import Server
from src.services.database import db_manager
from src.services.cache_manager import MultiLevelCache
from src.utils.logger import logger, LogArea


class DataService:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._servers_cache: Dict[str, Server] = {}
        self._blacklist_cache: Set[str] = set()
        self._blacklist_names_cache: Dict[str, str] = {}  # Store server names
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
        # Load all blacklist documents (array of objects with _id and server_name)
        self._blacklist_names_cache: Dict[str, str] = {}  # Store server names
        async for blacklist_doc in blacklist_collection.find():
            if "_id" in blacklist_doc:
                server_id = str(blacklist_doc["_id"])
                self._blacklist_cache.add(server_id)
                self._blacklist_names_cache[server_id] = blacklist_doc.get("server_name", "")

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
            
            # Clear existing blacklist
            await blacklist_collection.delete_many({})
            
            # Insert each blacklisted server as a separate document with its name
            if self._blacklist_cache:
                blacklist_docs = [
                    {"_id": server_id, "server_name": self._blacklist_names_cache.get(server_id, "")}
                    for server_id in self._blacklist_cache
                ]
                await blacklist_collection.insert_many(blacklist_docs)

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
            else:
                # Server already exists, update its name if different
                existing_server = self._servers_cache[server_id]
                if existing_server.server_name != server_name:
                    existing_server.server_name = server_name
                    servers_collection = db_manager.servers
                    await servers_collection.update_one(
                        {"_id": server_id},
                        {"$set": {"server_name": server_name}}
                    )
                    # Invalidate cache for this server
                    cache_key = f"server:{server_id}"
                    await self._cache.invalidate(cache_key)
            return self._servers_cache[server_id]
    
    async def update_server_name(self, server_id: str, server_name: str) -> bool:
        """Update the name of an existing server"""
        async with self._lock:
            if server_id in self._servers_cache:
                server = self._servers_cache[server_id]
                server.server_name = server_name
                
                servers_collection = db_manager.servers
                await servers_collection.update_one(
                    {"_id": server_id},
                    {"$set": {"server_name": server_name}}
                )
                
                # Invalidate cache for this server
                cache_key = f"server:{server_id}"
                await self._cache.invalidate(cache_key)
                return True
            return False
    
    async def remove_channel_subscription(self, server_id: str, channel_id: str) -> bool:
        """Remove a channel subscription from a server"""
        async with self._lock:
            server = self._servers_cache.get(server_id)
            if not server:
                return False
            
            # Remove channel from server
            if not server.remove_channel(channel_id):
                return False
            
            # Update database
            servers_collection = db_manager.servers
            await servers_collection.update_one(
                {"_id": server_id},
                {"$unset": {f"channels.{channel_id}": ""}}
            )
            
            # Invalidate cache for this server
            cache_key = f"server:{server_id}"
            await self._cache.invalidate(cache_key)
            
            logger.debug(LogArea.DATABASE, f"Removed channel {channel_id} from server {server_id}")
            return True

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

    async def add_to_blacklist(self, server_id: str, server_name: str = "Unknown") -> bool:
        async with self._lock:
            # Check if already in cache
            if server_id in self._blacklist_cache:
                return False
            
            # Check if already in database (in case cache is out of sync)
            blacklist_collection = db_manager.blacklist
            existing = await blacklist_collection.find_one({"_id": server_id})
            if existing:
                # Update cache to match database
                self._blacklist_cache.add(server_id)
                self._blacklist_names_cache[server_id] = existing.get("server_name", server_name)
                return False
            
            # Add to cache and database
            self._blacklist_cache.add(server_id)
            self._blacklist_names_cache[server_id] = server_name
            
            await blacklist_collection.insert_one(
                {"_id": server_id, "server_name": server_name}
            )
            
            # Invalidate cache
            cache_key = f"blacklist:{server_id}"
            await self._cache.invalidate(cache_key)
            return True

    async def remove_from_blacklist(self, server_id: str) -> bool:
        async with self._lock:
            if server_id in self._blacklist_cache:
                self._blacklist_cache.remove(server_id)
                if server_id in self._blacklist_names_cache:
                    del self._blacklist_names_cache[server_id]

                # Delete the document with this _id
                blacklist_collection = db_manager.blacklist
                await blacklist_collection.delete_one(
                    {"_id": server_id}
                )
                
                # Invalidate cache
                cache_key = f"blacklist:{server_id}"
                await self._cache.invalidate(cache_key)
                return True
            return False

    async def get_blacklist(self) -> List[str]:
        async with self._lock:
            return list(self._blacklist_cache)
    
    async def get_blacklist_with_names(self) -> Dict[str, str]:
        async with self._lock:
            return self._blacklist_names_cache.copy()

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
                # Ensure removed_at is timezone-aware
                if removed_at:
                    if removed_at.tzinfo is None:
                        removed_at = removed_at.replace(tzinfo=timezone.utc)
                    days_ago = (datetime.now(timezone.utc) - removed_at).days
                else:
                    days_ago = 30
                logger.info(
                    LogArea.CLEANUP,
                    f"Cleaned up server: {server_name} (ID: {server_id})"
                )
                cleaned_count += 1

        if cleaned_count > 0:
            logger.info(LogArea.CLEANUP, f"Total servers cleaned up: {cleaned_count}")

        return cleaned_count
