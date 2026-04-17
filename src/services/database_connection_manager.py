import os
from typing import Optional, Any, List
import asyncpg


class DatabaseManager:
    _instance: Optional["DatabaseManager"] = None
    _pool: Optional[asyncpg.Pool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = False

    async def connect(self) -> None:
        if self.initialized:
            return

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL not found in environment variables")

        self._pool = await asyncpg.create_pool(database_url)

        # Verify the connection works
        async with self._pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        from src.utils.logger import logger, LogArea

        logger.info(LogArea.DATABASE, "Successfully connected to PostgreSQL")

        self.initialized = True

    async def disconnect(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None
            self.initialized = False

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._pool

    async def execute(self, query: str, *args) -> str:
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    def acquire(self):
        return self._pool.acquire()


db_manager = DatabaseManager()
