from typing import Dict, List, Optional, Set, Any, Union
import asyncio
import discord
from datetime import datetime, timezone, timedelta

from src.models import Server, ChannelTimer, IgnoredEntities, BlacklistEntry, RemovedServer, BotConfigDocument
from src.services.database_connection_manager import db_manager
from src.services.cache_manager import MultiLevelCache
from src.utils.logger import logger, LogArea


class DataService:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._servers_cache: Dict[str, Server] = {}
        self._blacklist_cache: Set[str] = set()
        self._blacklist_names_cache: Dict[str, str] = {}
        self._blacklist_entries_cache: Dict[str, BlacklistEntry] = {}
        self._timezones_cache: Dict[str, str] = {}
        self._admins_cache: Set[str] = set()
        self._bot_config: Optional[BotConfigDocument] = None
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
        server_rows = await db_manager.fetch("SELECT * FROM servers")
        if not server_rows:
            return

        channel_rows = await db_manager.fetch("SELECT * FROM channels")
        ignored_msg_rows = await db_manager.fetch("SELECT * FROM ignored_messages")
        ignored_user_rows = await db_manager.fetch("SELECT * FROM ignored_users")

        # Group ignored data by (channel_id, server_id)
        ignored_msgs: Dict[tuple, List[str]] = {}
        for row in ignored_msg_rows:
            key = (row["channel_id"], row["server_id"])
            ignored_msgs.setdefault(key, []).append(row["message_id"])

        ignored_users_map: Dict[tuple, List[str]] = {}
        for row in ignored_user_rows:
            key = (row["channel_id"], row["server_id"])
            ignored_users_map.setdefault(key, []).append(row["user_id"])

        # Group channels by server_id
        channels_by_server: Dict[str, list] = {}
        for row in channel_rows:
            channels_by_server.setdefault(row["server_id"], []).append(row)

        for row in server_rows:
            server_id = row["server_id"]
            server = Server(
                server_id=server_id,
                server_name=row["server_name"] or "",
                timezone=row["timezone"],
                language=row["language"] or "en",
            )

            for ch_row in channels_by_server.get(server_id, []):
                channel_id = ch_row["channel_id"]
                key = (channel_id, server_id)
                ignored = IgnoredEntities(
                    messages=ignored_msgs.get(key, []),
                    users=ignored_users_map.get(key, []),
                )
                server.channels[channel_id] = ChannelTimer(
                    channel_id=channel_id,
                    timer=ch_row["timer"],
                    next_run_time=ch_row["next_run_time"],
                    ignored=ignored,
                    view_message_id=ch_row["view_message_id"],
                )

            self._servers_cache[server_id] = server

    async def _load_blacklist_from_database(self) -> None:
        self._blacklist_names_cache = {}
        self._blacklist_entries_cache = {}

        rows = await db_manager.fetch("SELECT * FROM blacklist")
        for row in rows:
            entry = BlacklistEntry(
                server_id=row["server_id"],
                server_name=row["server_name"] or "Unknown",
                blacklisted_at=row["blacklisted_at"],
                reason=row["reason"],
                blacklisted_by=row["blacklisted_by"],
            )
            self._blacklist_cache.add(entry.server_id)
            self._blacklist_names_cache[entry.server_id] = entry.server_name
            self._blacklist_entries_cache[entry.server_id] = entry

    async def _load_timezone_mappings_from_database(self) -> None:
        rows = await db_manager.fetch("SELECT abbreviation, timezone FROM config_timezones")
        self._timezones_cache = {row["abbreviation"]: row["timezone"] for row in rows}

    async def save_servers(self) -> None:
        async with self._lock:
            async with db_manager.pool.acquire() as conn:
                async with conn.transaction():
                    for server_id, server in self._servers_cache.items():
                        await conn.execute(
                            """
                            INSERT INTO servers (server_id, server_name, timezone, language)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT (server_id) DO UPDATE SET
                                server_name = EXCLUDED.server_name,
                                timezone    = EXCLUDED.timezone,
                                language    = EXCLUDED.language
                            """,
                            server_id,
                            server.server_name or "",
                            server.timezone,
                            server.language or "en",
                        )

                        existing_ids = {
                            r["channel_id"]
                            for r in await conn.fetch(
                                "SELECT channel_id FROM channels WHERE server_id = $1",
                                server_id,
                            )
                        }
                        current_ids = set(server.channels.keys())

                        # Delete channels that no longer exist (cascade removes ignored data)
                        for channel_id in existing_ids - current_ids:
                            await conn.execute(
                                "DELETE FROM channels WHERE channel_id = $1 AND server_id = $2",
                                channel_id,
                                server_id,
                            )

                        for channel_id, channel_timer in server.channels.items():
                            next_run = channel_timer.next_run_time
                            if next_run.tzinfo is None:
                                next_run = next_run.replace(tzinfo=timezone.utc)

                            await conn.execute(
                                """
                                INSERT INTO channels (channel_id, server_id, timer, next_run_time, view_message_id)
                                VALUES ($1, $2, $3, $4, $5)
                                ON CONFLICT (channel_id, server_id) DO UPDATE SET
                                    timer           = EXCLUDED.timer,
                                    next_run_time   = EXCLUDED.next_run_time,
                                    view_message_id = EXCLUDED.view_message_id
                                """,
                                channel_id,
                                server_id,
                                channel_timer.timer,
                                next_run,
                                channel_timer.view_message_id,
                            )

                            await conn.execute(
                                "DELETE FROM ignored_messages WHERE channel_id = $1 AND server_id = $2",
                                channel_id,
                                server_id,
                            )
                            if channel_timer.ignored.messages:
                                await conn.executemany(
                                    "INSERT INTO ignored_messages (channel_id, server_id, message_id) VALUES ($1, $2, $3)",
                                    [
                                        (channel_id, server_id, msg_id)
                                        for msg_id in channel_timer.ignored.messages
                                    ],
                                )

                            await conn.execute(
                                "DELETE FROM ignored_users WHERE channel_id = $1 AND server_id = $2",
                                channel_id,
                                server_id,
                            )
                            if channel_timer.ignored.users:
                                await conn.executemany(
                                    "INSERT INTO ignored_users (channel_id, server_id, user_id) VALUES ($1, $2, $3)",
                                    [
                                        (channel_id, server_id, user_id)
                                        for user_id in channel_timer.ignored.users
                                    ],
                                )

    async def save_blacklist(self) -> None:
        async with self._lock:
            async with db_manager.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("DELETE FROM blacklist")
                    if self._blacklist_entries_cache:
                        await conn.executemany(
                            """
                            INSERT INTO blacklist (server_id, server_name, blacklisted_at, reason, blacklisted_by)
                            VALUES ($1, $2, $3, $4, $5)
                            """,
                            [
                                (
                                    e.server_id,
                                    e.server_name,
                                    e.blacklisted_at,
                                    e.reason,
                                    e.blacklisted_by,
                                )
                                for e in self._blacklist_entries_cache.values()
                            ],
                        )

    async def get_server(self, server_id: str) -> Optional[Server]:
        cache_key = f"server:{server_id}"
        cached_server = await self._cache.get(cache_key)
        if cached_server is not None:
            return cached_server

        async with self._lock:
            if server_id in self._servers_cache:
                server = self._servers_cache[server_id]
                await self._cache.set(cache_key, server, cache_level="memory")
                return server

            row = await db_manager.fetchrow(
                "SELECT * FROM servers WHERE server_id = $1", server_id
            )
            if row:
                server = Server(
                    server_id=server_id,
                    server_name=row["server_name"] or "",
                    timezone=row["timezone"],
                    language=row["language"] or "en",
                )

                channel_rows = await db_manager.fetch(
                    """
                    SELECT c.*,
                        ARRAY_AGG(DISTINCT im.message_id) FILTER (WHERE im.message_id IS NOT NULL) AS ignored_messages,
                        ARRAY_AGG(DISTINCT iu.user_id)   FILTER (WHERE iu.user_id   IS NOT NULL) AS ignored_users
                    FROM channels c
                    LEFT JOIN ignored_messages im ON im.channel_id = c.channel_id AND im.server_id = c.server_id
                    LEFT JOIN ignored_users    iu ON iu.channel_id = c.channel_id AND iu.server_id = c.server_id
                    WHERE c.server_id = $1
                    GROUP BY c.channel_id, c.server_id, c.timer, c.next_run_time, c.view_message_id
                    """,
                    server_id,
                )

                for ch_row in channel_rows:
                    channel_id = ch_row["channel_id"]
                    ignored = IgnoredEntities(
                        messages=list(ch_row["ignored_messages"] or []),
                        users=list(ch_row["ignored_users"] or []),
                    )
                    server.channels[channel_id] = ChannelTimer(
                        channel_id=channel_id,
                        timer=ch_row["timer"],
                        next_run_time=ch_row["next_run_time"],
                        ignored=ignored,
                        view_message_id=ch_row["view_message_id"],
                    )

                self._servers_cache[server_id] = server
                await self._cache.set(cache_key, server, cache_level="warm")
                return server
            return None

    async def add_server(self, guild: discord.Guild) -> Server:
        server_id = str(guild.id)
        server_name = guild.name

        async with self._lock:
            if server_id not in self._servers_cache:
                server = Server(server_id, server_name)
                if not server.timezone:
                    detected_tz = self._auto_detect_timezone(guild)
                    if detected_tz:
                        server.timezone = detected_tz
                if not server.language:
                    server.language = "en"
                self._servers_cache[server_id] = server

                await db_manager.execute(
                    """
                    INSERT INTO servers (server_id, server_name, timezone, language)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (server_id) DO NOTHING
                    """,
                    server_id,
                    server.server_name or "",
                    server.timezone,
                    server.language,
                )

                cache_key = f"server:{server_id}"
                await self._cache.invalidate(cache_key)
            else:
                existing_server = self._servers_cache[server_id]
                updated = False
                if existing_server.server_name != server_name:
                    existing_server.server_name = server_name
                    updated = True
                if not existing_server.timezone:
                    detected_tz = self._auto_detect_timezone(guild)
                    if detected_tz:
                        existing_server.timezone = detected_tz
                        updated = True
                if updated:
                    await db_manager.execute(
                        "UPDATE servers SET server_name = $1, timezone = $2 WHERE server_id = $3",
                        server_name,
                        existing_server.timezone,
                        server_id,
                    )
                    cache_key = f"server:{server_id}"
                    await self._cache.invalidate(cache_key)

            return self._servers_cache[server_id]

    async def update_server_name(self, server_id: str, server_name: str) -> bool:
        async with self._lock:
            if server_id in self._servers_cache:
                self._servers_cache[server_id].server_name = server_name

                await db_manager.execute(
                    "UPDATE servers SET server_name = $1 WHERE server_id = $2",
                    server_name,
                    server_id,
                )

                cache_key = f"server:{server_id}"
                await self._cache.invalidate(cache_key)
                return True
            return False

    async def remove_channel_subscription(
        self, server_id: str, channel_id: str
    ) -> bool:
        async with self._lock:
            server = self._servers_cache.get(server_id)
            if not server:
                return False

            if not server.remove_channel(channel_id):
                return False

            # Cascade on the FK handles ignored_messages and ignored_users
            await db_manager.execute(
                "DELETE FROM channels WHERE channel_id = $1 AND server_id = $2",
                channel_id,
                server_id,
            )

            cache_key = f"server:{server_id}"
            await self._cache.invalidate(cache_key)

            logger.debug(
                LogArea.DATABASE,
                f"Removed channel {channel_id} from server {server_id}",
            )
            return True

    async def get_all_servers(self) -> Dict[str, Server]:
        async with self._lock:
            return self._servers_cache.copy()

    async def is_blacklisted(self, server_id: str) -> bool:
        cache_key = f"blacklist:{server_id}"
        cached_result = await self._cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        async with self._lock:
            result = server_id in self._blacklist_cache
            await self._cache.set(cache_key, result, cache_level="warm", ttl=600)
            return result

    async def add_to_blacklist(
        self,
        server_id: str,
        server_name: str = "Unknown",
        reason: str = "No reason provided",
        blacklisted_by: Optional[str] = None,
    ) -> bool:
        async with self._lock:
            if server_id in self._blacklist_cache:
                return False

            existing = await db_manager.fetchrow(
                "SELECT server_id FROM blacklist WHERE server_id = $1", server_id
            )
            if existing:
                entry = BlacklistEntry(server_id=server_id, server_name=server_name)
                self._blacklist_cache.add(entry.server_id)
                self._blacklist_names_cache[entry.server_id] = entry.server_name
                return False

            entry = BlacklistEntry(
                server_id=server_id,
                server_name=server_name,
                reason=reason,
                blacklisted_by=blacklisted_by,
            )
            self._blacklist_cache.add(entry.server_id)
            self._blacklist_names_cache[entry.server_id] = entry.server_name
            self._blacklist_entries_cache[entry.server_id] = entry

            await db_manager.execute(
                """
                INSERT INTO blacklist (server_id, server_name, blacklisted_at, reason, blacklisted_by)
                VALUES ($1, $2, $3, $4, $5)
                """,
                entry.server_id,
                entry.server_name,
                entry.blacklisted_at,
                entry.reason,
                entry.blacklisted_by,
            )

            cache_key = f"blacklist:{server_id}"
            await self._cache.invalidate(cache_key)
            return True

    async def remove_from_blacklist(self, server_id: str) -> bool:
        async with self._lock:
            if server_id in self._blacklist_cache:
                self._blacklist_cache.remove(server_id)
                self._blacklist_names_cache.pop(server_id, None)
                self._blacklist_entries_cache.pop(server_id, None)

                await db_manager.execute(
                    "DELETE FROM blacklist WHERE server_id = $1", server_id
                )

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
        async with self._lock:
            return self._blacklist_entries_cache.copy()

    def get_timezone(self, timezone_abbr: str) -> Optional[str]:
        return self._timezones_cache.get(timezone_abbr)

    def get_timezones_list(self) -> Dict[str, str]:
        return self._timezones_cache.copy()

    async def set_server_timezone(self, server_id: str, timezone_str: str) -> None:
        server = await self.get_server(server_id)
        if server:
            server.timezone = timezone_str
            await self.save_servers()

    async def get_server_timezone(self, server_id: str) -> Optional[str]:
        server = await self.get_server(server_id)
        if server and server.timezone:
            return server.timezone
        return None

    async def set_server_language(self, server_id: str, language: str) -> None:
        server = await self.get_server(server_id)
        if server:
            server.language = language
            await self.save_servers()
            cache_key = f"server:{server_id}"
            await self._cache.invalidate(cache_key)

    async def get_server_language(self, server_id: str) -> Optional[str]:
        server = await self.get_server(server_id)
        if server and server.language:
            return server.language
        return None

    def get_timezone_for_server(
        self, server_id: str, timezone_abbr: str = None
    ) -> Optional[str]:
        if server_id in self._servers_cache:
            server = self._servers_cache[server_id]
            if server.timezone:
                return server.timezone

        if timezone_abbr:
            return self._timezones_cache.get(timezone_abbr)

        return "UTC"

    async def get_removed_server(self, server_id: str) -> Optional[RemovedServer]:
        cache_key = f"removed_server:{server_id}"
        cached_doc = await self._cache.get(cache_key)
        if cached_doc is not None:
            return cached_doc

        row = await db_manager.fetchrow(
            "SELECT * FROM removed_servers WHERE server_id = $1", server_id
        )
        if row:
            removed_server = RemovedServer(
                server_id=row["server_id"],
                server_name=row["server_name"],
                removed_at=row["removed_at"],
                removal_reason=row["removal_reason"],
            )
            await self._cache.set(
                cache_key, removed_server, cache_level="cold", ttl=1800
            )
            return removed_server
        return None

    async def cache_removed_server(
        self, server_id: str, server_doc: Union[RemovedServer, Dict[str, Any]]
    ) -> None:
        cache_key = f"removed_server:{server_id}"
        if isinstance(server_doc, dict):
            removed_server = RemovedServer.from_dict(server_doc)
        else:
            removed_server = server_doc
        await self._cache.set(cache_key, removed_server, cache_level="cold", ttl=1800)

    async def invalidate_removed_server_cache(self, server_id: str) -> None:
        cache_key = f"removed_server:{server_id}"
        await self._cache.invalidate(cache_key)

    def get_cache_stats(self) -> Dict[str, Any]:
        return self._cache.get_all_stats()

    async def cleanup_old_removed_servers(self) -> int:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

        rows = await db_manager.fetch(
            "SELECT * FROM removed_servers WHERE removed_at < $1", cutoff_date
        )

        cleaned_count = 0

        for row in rows:
            server_id = row["server_id"]
            server_name = row["server_name"]
            removed_at = row["removed_at"]

            result = await db_manager.execute(
                "DELETE FROM servers WHERE server_id = $1", server_id
            )

            if server_id in self._servers_cache:
                del self._servers_cache[server_id]

            await db_manager.execute(
                "DELETE FROM removed_servers WHERE server_id = $1", server_id
            )

            if result == "DELETE 1":
                days_ago = (datetime.now(timezone.utc) - removed_at).days if removed_at else 30
                logger.info(
                    LogArea.CLEANUP,
                    f"Cleaned up server: {server_name} (ID: {server_id})",
                )
                cleaned_count += 1

        if cleaned_count > 0:
            logger.info(LogArea.CLEANUP, f"Total servers cleaned up: {cleaned_count}")

        return cleaned_count

    async def _load_bot_config_from_database(self) -> None:
        admin_rows = await db_manager.fetch("SELECT user_id FROM config_admins")
        admin_list = [row["user_id"] for row in admin_rows]

        self._bot_config = BotConfigDocument(
            admins=admin_list,
            timezones=self._timezones_cache,
        )
        self._admins_cache = set(admin_list)

    async def save_bot_config(self) -> None:
        if not self._bot_config:
            return

        async with db_manager.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("DELETE FROM config_admins")
                if self._bot_config.admins:
                    await conn.executemany(
                        "INSERT INTO config_admins (user_id) VALUES ($1)",
                        [(user_id,) for user_id in self._bot_config.admins],
                    )

    async def is_admin(self, user_id: str) -> bool:
        return user_id in self._admins_cache

    async def get_admins(self) -> Set[str]:
        return self._admins_cache.copy()

    async def add_admin(self, user_id: str) -> bool:
        async with self._lock:
            if not self._bot_config:
                self._bot_config = BotConfigDocument()

            if user_id in self._admins_cache:
                return False

            if self._bot_config.add_admin(user_id):
                self._admins_cache.add(user_id)
                await self.save_bot_config()
                logger.info(LogArea.DATABASE, f"Added admin: {user_id}")
                return True
            return False

    async def remove_admin(self, user_id: str) -> bool:
        async with self._lock:
            if not self._bot_config:
                self._bot_config = BotConfigDocument()

            if user_id not in self._admins_cache:
                return False

            if self._bot_config.remove_admin(user_id):
                self._admins_cache.discard(user_id)
                await self.save_bot_config()
                logger.info(LogArea.DATABASE, f"Removed admin: {user_id}")
                return True
            return False

    async def reload_timezones_cache(self) -> None:
        async with self._lock:
            await self._load_timezone_mappings_from_database()
            logger.info(
                LogArea.DATABASE,
                f"Reloaded {len(self._timezones_cache)} timezone mapping(s) from database",
            )

    def _auto_detect_timezone(self, guild: discord.Guild) -> Optional[str]:
        region_timezone_map = {
            "us-west": "America/Los_Angeles",
            "us-central": "America/Chicago",
            "us-east": "America/New_York",
            "us-south": "America/Chicago",
            "europe": "Europe/London",
            "eu-west": "Europe/London",
            "eu-central": "Europe/Berlin",
            "london": "Europe/London",
            "frankfurt": "Europe/Berlin",
            "amsterdam": "Europe/Amsterdam",
            "russia": "Europe/Moscow",
            "hongkong": "Asia/Hong_Kong",
            "singapore": "Asia/Singapore",
            "sydney": "Australia/Sydney",
            "japan": "Asia/Tokyo",
            "india": "Asia/Kolkata",
            "dubai": "Asia/Dubai",
            "south-korea": "Asia/Seoul",
            "brazil": "America/Sao_Paulo",
            "argentina": "America/Argentina/Buenos_Aires",
            "southafrica": "Africa/Johannesburg",
        }

        detected_timezone = None

        if hasattr(guild, "region") and guild.region:
            region_str = str(guild.region).lower()
            for region_key, tz in region_timezone_map.items():
                if region_key in region_str:
                    detected_timezone = tz
                    break

        if not detected_timezone and guild.voice_channels:
            for vc in guild.voice_channels:
                if hasattr(vc, "rtc_region") and vc.rtc_region:
                    region_str = str(vc.rtc_region).lower()
                    for region_key, tz in region_timezone_map.items():
                        if region_key in region_str:
                            detected_timezone = tz
                            break
                    if detected_timezone:
                        break

        return detected_timezone

    async def reload_all_caches(self) -> None:
        async with self._lock:
            await self._cache.clear_all()

            self._servers_cache.clear()
            await self._load_all_servers_from_database()

            self._blacklist_cache.clear()
            self._blacklist_names_cache.clear()
            self._blacklist_entries_cache.clear()
            await self._load_blacklist_from_database()

            logger.info(
                LogArea.DATABASE, "Reloaded all caches (except admins and timezones)"
            )
