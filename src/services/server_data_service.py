from typing import Dict, List, Optional, Set, Any
import asyncio
import discord
from datetime import datetime, timezone, timedelta

from src.models import (
    Server, 
    BlacklistEntry, 
    RemovedServer,
    BotConfigDocument
)
from src.services.database_connection_manager import db_manager
from src.services.cache_manager import MultiLevelCache
from src.utils.logger import logger, LogArea


class DataService:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._servers_cache: Dict[str, Server] = {}
        self._blacklist_cache: Set[str] = set()
        self._blacklist_names_cache: Dict[str, str] = {}  # Store server names
        self._blacklist_entries_cache: Dict[str, BlacklistEntry] = {}  # Store full entries
        self._timezones_cache: Dict[str, str] = {}
        self._admins_cache: Set[str] = set()  # Cache for admin user IDs
        self._bot_config: Optional[BotConfigDocument] = None  # Bot config document
        self._cache = MultiLevelCache()
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return

        async with self._lock:
            await self._load_all_servers_from_database()
            await self._load_blacklist_from_database()
            await self._load_timezone_mappings_from_database()
            await self._load_bot_config_from_database()
            self._initialized = True

    async def _load_all_servers_from_database(self) -> None:
        servers_collection = db_manager.servers
        async for server_doc in servers_collection.find():
            server_id = str(server_doc["_id"])
            self._servers_cache[server_id] = Server.from_dict(server_id, server_doc)

    async def _load_blacklist_from_database(self) -> None:
        blacklist_collection = db_manager.blacklist
        # Load all blacklist documents as BlacklistEntry models
        self._blacklist_names_cache: Dict[str, str] = {}  # Store server names
        self._blacklist_entries_cache: Dict[str, BlacklistEntry] = {}  # Store full entries
        async for blacklist_doc in blacklist_collection.find():
            if "_id" in blacklist_doc:
                entry = BlacklistEntry.from_dict(blacklist_doc)
                self._blacklist_cache.add(entry.server_id)
                self._blacklist_names_cache[entry.server_id] = entry.server_name
                self._blacklist_entries_cache[entry.server_id] = entry

    async def _load_timezone_mappings_from_database(self) -> None:
        config_collection = db_manager.config
        config_doc = await config_collection.find_one({"_id": "bot_config"})
        if config_doc and "timezones" in config_doc:
            self._timezones_cache = config_doc["timezones"]
        else:
            self._timezones_cache = {}

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
            
            # Insert each blacklisted server as a BlacklistEntry document
            if self._blacklist_entries_cache:
                blacklist_entries = [
                    entry.to_dict()
                    for entry in self._blacklist_entries_cache.values()
                ]
                await blacklist_collection.insert_many(blacklist_entries)

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

    async def add_server(self, guild: discord.Guild) -> Server:
        """Add or update a server from a guild object"""
        server_id = str(guild.id)
        server_name = guild.name
        
        async with self._lock:
            if server_id not in self._servers_cache:
                server = Server(server_id, server_name)
                # Auto-detect timezone for new servers
                if not server.timezone:
                    detected_tz = self._auto_detect_timezone(guild)
                    if detected_tz:
                        server.timezone = detected_tz
                        server.timezone_auto_detected = True
                # Set default language to English if not set
                if not server.language:
                    server.language = "en"
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
                updated = False
                if existing_server.server_name != server_name:
                    existing_server.server_name = server_name
                    updated = True
                # Auto-detect timezone if not set
                if not existing_server.timezone:
                    detected_tz = self._auto_detect_timezone(guild)
                    if detected_tz:
                        existing_server.timezone = detected_tz
                        existing_server.timezone_auto_detected = True
                        updated = True
                if updated:
                    servers_collection = db_manager.servers
                    await servers_collection.update_one(
                        {"_id": server_id},
                        {"$set": {"server_name": server_name, "timezone": existing_server.timezone, "timezone_auto_detected": existing_server.timezone_auto_detected}}
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

    async def add_to_blacklist(self, server_id: str, server_name: str = "Unknown", reason: str = "No reason provided", blacklisted_by: Optional[str] = None) -> bool:
        async with self._lock:
            # Check if already in cache
            if server_id in self._blacklist_cache:
                return False
            
            # Check if already in database (in case cache is out of sync)
            blacklist_collection = db_manager.blacklist
            existing = await blacklist_collection.find_one({"_id": server_id})
            if existing:
                # Update cache to match database
                entry = BlacklistEntry.from_dict(existing)
                self._blacklist_cache.add(entry.server_id)
                self._blacklist_names_cache[entry.server_id] = entry.server_name
                return False
            
            # Add to cache and database
            entry = BlacklistEntry(
                server_id=server_id, 
                server_name=server_name,
                reason=reason,
                blacklisted_by=blacklisted_by
            )
            self._blacklist_cache.add(entry.server_id)
            self._blacklist_names_cache[entry.server_id] = entry.server_name
            self._blacklist_entries_cache[entry.server_id] = entry
            
            await blacklist_collection.insert_one(entry.to_dict())
            
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
                if server_id in self._blacklist_entries_cache:
                    del self._blacklist_entries_cache[server_id]

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
    
    async def get_blacklist_entries(self) -> Dict[str, BlacklistEntry]:
        """Get full blacklist entries with all data"""
        async with self._lock:
            return self._blacklist_entries_cache.copy()

    def get_timezone(self, timezone_abbr: str) -> Optional[str]:
        return self._timezones_cache.get(timezone_abbr)
    
    def get_timezones_list(self) -> Dict[str, str]:
        """Get all available timezone mappings from config"""
        return self._timezones_cache.copy()
    
    async def set_server_timezone(self, server_id: str, timezone_str: str, auto_detected: bool = False) -> None:
        """Set or update the timezone for a specific server"""
        server = await self.get_server(server_id)
        if server:
            server.timezone = timezone_str
            server.timezone_auto_detected = auto_detected
            await self.save_servers()
    
    async def get_server_timezone(self, server_id: str) -> Optional[str]:
        """Get the timezone setting for a specific server"""
        server = await self.get_server(server_id)
        if server and server.timezone:
            return server.timezone
        return None
    
    async def set_server_language(self, server_id: str, language: str) -> None:
        """Set or update the language for a specific server"""
        server = await self.get_server(server_id)
        if server:
            server.language = language
            await self.save_servers()
            # Invalidate cache for this server
            cache_key = f"server:{server_id}"
            await self._cache.invalidate(cache_key)
    
    async def get_server_language(self, server_id: str) -> Optional[str]:
        """Get the language setting for a specific server"""
        server = await self.get_server(server_id)
        if server and server.language:
            return server.language
        return None
    
    def get_timezone_for_server(self, server_id: str, timezone_abbr: str = None) -> Optional[str]:
        """Get timezone for a server, with fallback to abbreviation mapping or UTC"""
        # First check if server has a specific timezone set
        if server_id in self._servers_cache:
            server = self._servers_cache[server_id]
            if server.timezone:
                return server.timezone
        
        # If timezone abbreviation provided, check mapping
        if timezone_abbr:
            return self._timezones_cache.get(timezone_abbr)
        
        # Default to UTC
        return "UTC"
    
    async def get_removed_server(self, server_id: str) -> Optional[RemovedServer]:
        cache_key = f"removed_server:{server_id}"
        cached_doc = await self._cache.get(cache_key)
        if cached_doc is not None:
            return cached_doc
        
        removed_servers_collection = db_manager.removed_servers
        doc = await removed_servers_collection.find_one({"_id": server_id})
        if doc:
            removed_server = RemovedServer.from_dict(doc)
            await self._cache.set(cache_key, removed_server, cache_level="cold", ttl=1800)  # 30 minutes
            return removed_server
        return None
    
    async def cache_removed_server(self, server_id: str, server_doc: Dict[str, Any]) -> None:
        cache_key = f"removed_server:{server_id}"
        removed_server = RemovedServer.from_dict(server_doc) if isinstance(server_doc, dict) else server_doc
        await self._cache.set(cache_key, removed_server, cache_level="cold", ttl=1800)
    
    async def invalidate_removed_server_cache(self, server_id: str) -> None:
        cache_key = f"removed_server:{server_id}"
        await self._cache.invalidate(cache_key)
    
    def get_cache_stats(self) -> Dict[str, Any]:
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
            removed_server = RemovedServer.from_dict(server_doc)
            server_id = removed_server.server_id
            server_name = removed_server.server_name
            removed_at = removed_server.removed_at

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
    
    async def _load_bot_config_from_database(self) -> None:
        """Load bot config including admins from database"""
        config_collection = db_manager.config
        config_doc = await config_collection.find_one({"_id": "bot_config"})
        
        if config_doc:
            self._bot_config = BotConfigDocument.from_dict(config_doc)
            # Cache all admin IDs
            self._admins_cache = set(self._bot_config.admins)
        else:
            # Create default config if none exists
            self._bot_config = BotConfigDocument()
            await self.save_bot_config()
    
    async def save_bot_config(self) -> None:
        """Save bot config to database"""
        if not self._bot_config:
            return
        
        # Don't acquire lock here - it should already be held by the caller
        config_collection = db_manager.config
        config_data = self._bot_config.to_dict()
        
        await config_collection.replace_one(
            {"_id": "bot_config"},
            config_data,
            upsert=True
        )
    
    async def is_admin(self, user_id: str) -> bool:
        """Check if a user is an admin (uses cache)"""
        return user_id in self._admins_cache
    
    async def get_admins(self) -> Set[str]:
        """Get all admin IDs (from cache)"""
        return self._admins_cache.copy()
    
    async def add_admin(self, user_id: str) -> bool:
        """Add a new admin"""
        async with self._lock:
            # Ensure config is initialized
            if not self._bot_config:
                self._bot_config = BotConfigDocument()
            
            if user_id in self._admins_cache:
                return False
            
            # Add to config document
            if self._bot_config.add_admin(user_id):
                # Update cache
                self._admins_cache.add(user_id)
                
                # Save to database
                await self.save_bot_config()
                
                logger.info(LogArea.DATABASE, f"Added admin: {user_id}")
                return True
            return False
    
    async def remove_admin(self, user_id: str) -> bool:
        """Remove an admin"""
        async with self._lock:
            # Ensure config is initialized
            if not self._bot_config:
                self._bot_config = BotConfigDocument()
            
            if user_id not in self._admins_cache:
                return False
            
            # Remove from config document
            if self._bot_config.remove_admin(user_id):
                # Update cache
                self._admins_cache.discard(user_id)
                
                # Save to database
                await self.save_bot_config()
                
                logger.info(LogArea.DATABASE, f"Removed admin: {user_id}")
                return True
            return False
    
    async def reload_admins_cache(self) -> None:
        """Reload admins cache from database"""
        async with self._lock:
            config_collection = db_manager.config
            config_doc = await config_collection.find_one({"_id": "bot_config"})
            
            if config_doc:
                self._bot_config = BotConfigDocument.from_dict(config_doc)
                self._admins_cache = set(self._bot_config.admins)
                logger.info(LogArea.DATABASE, f"Reloaded {len(self._admins_cache)} admin(s) from database")
            else:
                self._bot_config = BotConfigDocument()
                self._admins_cache = set()
                logger.warning(LogArea.DATABASE, "No bot config found in database during reload")
    
    async def reload_timezones_cache(self) -> None:
        """Reload timezones cache from database"""
        async with self._lock:
            await self._load_timezone_mappings_from_database()
            logger.info(LogArea.DATABASE, f"Reloaded {len(self._timezones_cache)} timezone mapping(s) from database")
    
    def _auto_detect_timezone(self, guild: discord.Guild) -> Optional[str]:
        """Auto-detect timezone based on guild region"""
        region_timezone_map = {
            # US regions
            'us-west': 'America/Los_Angeles',
            'us-central': 'America/Chicago',
            'us-east': 'America/New_York',
            'us-south': 'America/Chicago',
            
            # Europe regions
            'europe': 'Europe/London',
            'eu-west': 'Europe/London',
            'eu-central': 'Europe/Berlin',
            'london': 'Europe/London',
            'frankfurt': 'Europe/Berlin',
            'amsterdam': 'Europe/Amsterdam',
            'russia': 'Europe/Moscow',
            
            # Asia regions
            'hongkong': 'Asia/Hong_Kong',
            'singapore': 'Asia/Singapore',
            'sydney': 'Australia/Sydney',
            'japan': 'Asia/Tokyo',
            'india': 'Asia/Kolkata',
            'dubai': 'Asia/Dubai',
            'south-korea': 'Asia/Seoul',
            
            # South America
            'brazil': 'America/Sao_Paulo',
            'argentina': 'America/Argentina/Buenos_Aires',
            
            # South Africa
            'southafrica': 'Africa/Johannesburg',
        }
        
        detected_timezone = None
        
        # Try to get region from guild
        if hasattr(guild, 'region') and guild.region:
            region_str = str(guild.region).lower()
            for region_key, tz in region_timezone_map.items():
                if region_key in region_str:
                    detected_timezone = tz
                    break
        
        # If no region detected, try to use the first voice channel's region
        if not detected_timezone and guild.voice_channels:
            for vc in guild.voice_channels:
                if hasattr(vc, 'rtc_region') and vc.rtc_region:
                    region_str = str(vc.rtc_region).lower()
                    for region_key, tz in region_timezone_map.items():
                        if region_key in region_str:
                            detected_timezone = tz
                            break
                    if detected_timezone:
                        break
        
        return detected_timezone
    
    async def reload_all_caches(self) -> None:
        """Reload all caches except admins and timezones"""
        async with self._lock:
            # Clear multi-level cache
            await self._cache.clear_all()
            
            # Clear and reload servers
            self._servers_cache.clear()
            await self._load_all_servers_from_database()
            
            # Clear and reload blacklist
            self._blacklist_cache.clear()
            self._blacklist_names_cache.clear()
            self._blacklist_entries_cache.clear()
            await self._load_blacklist_from_database()
            
            logger.info(LogArea.DATABASE, "Reloaded all caches (except admins and timezones)")
    
