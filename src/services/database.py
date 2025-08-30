import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional


class DatabaseManager:
    _instance: Optional["DatabaseManager"] = None
    _client: Optional[AsyncIOMotorClient] = None
    _database = None

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

        self._client = AsyncIOMotorClient(database_url)
        self._database = self._client.get_default_database()

        await self._client.admin.command("ping")
        print("Successfully connected to MongoDB")

        self.initialized = True

    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            self.initialized = False

    @property
    def db(self):
        if self._database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._database

    @property
    def servers(self):
        return self.db.servers

    @property
    def timezones(self):
        return self.db.timezones

    @property
    def blacklist(self):
        return self.db.blacklist

    @property
    def removed_servers(self):
        return self.db.removed_servers


db_manager = DatabaseManager()
