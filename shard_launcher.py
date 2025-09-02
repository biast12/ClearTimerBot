#!/usr/bin/env python3
"""
Sharding launcher for ClearTimer Bot
Manages multiple bot shards for handling large numbers of servers
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import ConfigManager
from src.utils.logger import logger, LogArea

# Import discord to check recommended shard count
import discord


class ShardLauncher:
    """Manages bot sharding"""
    
    def __init__(self, shard_count: Optional[int] = None, shard_ids: Optional[list] = None):
        """
        Initialize the shard launcher
        
        Args:
            shard_count: Total number of shards (None for auto-detection)
            shard_ids: List of shard IDs to run on this process (None for all)
        """
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.shard_count = shard_count
        self.shard_ids = shard_ids
        self.processes = []
    
    async def get_recommended_shards(self) -> int:
        """Get the recommended number of shards from Discord"""
        try:
            # Create a temporary client just to get shard count
            client = discord.Client(intents=discord.Intents.default())
            
            # Get recommended shard count
            shard_count = await client.fetch_recommended_shard_count()
            
            await client.close()
            
            logger.info(LogArea.STARTUP, f"Discord recommends {shard_count} shard(s)")
            return shard_count
            
        except Exception as e:
            logger.error(LogArea.STARTUP, f"Failed to get recommended shard count: {e}")
            # Default to 1 shard if we can't get recommendation
            return 1
    
    async def launch_shard(self, shard_id: int, shard_count: int):
        """Launch a single shard as a subprocess"""
        logger.info(LogArea.STARTUP, f"Launching shard {shard_id}/{shard_count - 1}")
        
        # Set environment variables for the shard
        env = os.environ.copy()
        env['SHARD_ID'] = str(shard_id)
        env['SHARD_COUNT'] = str(shard_count)
        
        # Launch the shard process
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            'main.py',
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        self.processes.append(process)
        
        # Monitor the process output
        async def monitor_output(stream, prefix):
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode('utf-8').strip()
                if decoded:
                    print(f"[Shard {shard_id}] {decoded}")
        
        # Start monitoring tasks
        asyncio.create_task(monitor_output(process.stdout, "OUT"))
        asyncio.create_task(monitor_output(process.stderr, "ERR"))
        
        return process
    
    async def run(self):
        """Run the shard launcher"""
        try:
            # Determine shard count
            if self.shard_count is None:
                self.shard_count = await self.get_recommended_shards()
                logger.info(LogArea.STARTUP, f"Auto-detected shard count: {self.shard_count}")
            else:
                logger.info(LogArea.STARTUP, f"Using manual shard count: {self.shard_count}")
            
            # If only 1 shard needed, just run the bot normally
            if self.shard_count == 1:
                logger.info(LogArea.STARTUP, "Running in single-shard mode")
                # Import and run the bot directly
                from main import main
                await main()
                return
            
            # Determine which shards to run
            if self.shard_ids is None:
                self.shard_ids = list(range(self.shard_count))
            
            logger.info(LogArea.STARTUP, f"Launching {len(self.shard_ids)} shard(s): {self.shard_ids}")
            
            # Launch all shards
            tasks = []
            for shard_id in self.shard_ids:
                process = await self.launch_shard(shard_id, self.shard_count)
                tasks.append(process.wait())
            
            # Wait for all shards to complete
            logger.info(LogArea.STARTUP, "All shards launched, monitoring...")
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            logger.info(LogArea.STARTUP, "Received shutdown signal, stopping all shards...")
            for process in self.processes:
                process.terminate()
            await asyncio.gather(*[p.wait() for p in self.processes], return_exceptions=True)
        except Exception as e:
            logger.error(LogArea.STARTUP, f"Fatal error in shard launcher: {e}")
            raise
        finally:
            logger.info(LogArea.STARTUP, "Shard launcher shutdown complete")


async def main():
    """Main entry point for shard launcher"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ClearTimer Bot Shard Launcher')
    parser.add_argument('--shards', type=int, help='Total number of shards (auto-detect if not specified)')
    parser.add_argument('--shard-ids', type=str, help='Comma-separated list of shard IDs to run (all if not specified)')
    
    args = parser.parse_args()
    
    # Parse shard IDs if provided
    shard_ids = None
    if args.shard_ids:
        shard_ids = [int(x.strip()) for x in args.shard_ids.split(',')]
    
    # Create and run launcher
    launcher = ShardLauncher(shard_count=args.shards, shard_ids=shard_ids)
    await launcher.run()


if __name__ == "__main__":
    # Set up asyncio for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the launcher
    asyncio.run(main())