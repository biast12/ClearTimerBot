import discord
from discord.ext import commands
from typing import Optional

from src.core.config import BotConfig
from src.services.data_service import DataService
from src.services.scheduler_service import SchedulerService
from src.services.message_service import MessageService


class ClearTimerBot(commands.Bot):
    def __init__(self, config: BotConfig):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        self.config = config
        self.data_service = DataService()
        self.scheduler_service = SchedulerService(self.data_service)
        self.message_service = MessageService(self.data_service, self.scheduler_service)
        
        # Set up service callbacks
        self.scheduler_service.set_clear_callback(self.message_service.clear_channel_messages)
        self.scheduler_service.set_notify_callback(self.message_service.notify_missed_clear)
        
        self.version = "2.0.0"
    
    async def setup_hook(self) -> None:
        # Initialize services
        await self.data_service.initialize()
        
        # Load command cogs
        await self.load_commands()
    
    async def on_ready(self) -> None:
        print(f"Bot ready: {self.user} (ID: {self.user.id})")
        print(f"Version: {self.version}")
        print(f"Connected to {len(self.guilds)} guilds")
        
        # Set presence
        activity = discord.Game(name="Cleaning up the mess! 🧹")
        await self.change_presence(activity=activity)
        
        # Start scheduler and initialize jobs
        await self.scheduler_service.start()
        await self.scheduler_service.initialize_jobs(self)
        
        print("Bot initialization complete!")
    
    async def load_commands(self) -> None:
        # Load standard commands
        command_modules = [
            "src.commands.subscription",
            "src.commands.information",
            "src.commands.utility"
        ]
        
        for module in command_modules:
            try:
                await self.load_extension(module)
                print(f"Loaded extension: {module}")
            except Exception as e:
                print(f"Failed to load extension {module}: {e}")
        
        # Load owner commands if configured
        if self.config.is_owner_mode:
            try:
                await self.load_extension("src.commands.owner")
                print("Loaded owner commands")
            except Exception as e:
                print(f"Failed to load owner commands: {e}")
    
    async def close(self) -> None:
        await self.scheduler_service.shutdown()
        await super().close()
    
    def is_owner(self, user: discord.User) -> bool:
        if self.config.owner_id:
            return user.id == self.config.owner_id
        return False