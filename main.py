#!/usr/bin/env python3
"""
ClearTimer Bot - A Discord bot for automatic message clearing
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional, Dict
import argparse
from datetime import datetime, timezone

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import ConfigManager  # noqa: E402
from src.utils.logger import logger, LogArea  # noqa: E402
from src.services.database_connection_manager import db_manager  # noqa: E402

# Import discord to check recommended shard count
import discord  # noqa: E402


class ShardManager:
    """Manages bot sharding and process launching"""
    
    def __init__(self, shard_count: Optional[int] = None, shard_ids: Optional[list] = None, no_shard: bool = False, original_args: Optional[list] = None):
        """
        Initialize the shard manager
        
        Args:
            shard_count: Total number of shards (None for auto-detection)
            shard_ids: List of shard IDs to run on this process (None for all)
            no_shard: Force single-instance mode without sharding
            original_args: Original command-line arguments to preserve on restart
        """
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.shard_count = shard_count
        self.shard_ids = shard_ids
        self.no_shard = no_shard
        self.original_args = original_args or []  # Store original command-line arguments
        self.processes: Dict[int, asyncio.subprocess.Process] = {}
        self.shard_restart_counts: Dict[int, int] = {}
        self.max_restart_attempts = 3
        self.restart_cooldown = 30  # seconds
        self.should_restart = False  # Flag for full manager restart
        self.restart_event = asyncio.Event()  # Event to signal restart
    
    async def get_recommended_shards(self) -> int:
        """Get the recommended number of shards from Discord"""
        if self.no_shard:
            return 1
            
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
    
    async def launch_shard(self, shard_id: int, shard_count: int, auto_restart: bool = True):
        """Launch a single shard as a subprocess"""
        logger.info(LogArea.STARTUP, f"Launching shard {shard_id}/{shard_count - 1}")
        
        # Set environment variables for the shard
        env = os.environ.copy()
        env['SHARD_ID'] = str(shard_id)
        env['SHARD_COUNT'] = str(shard_count)
        
        # Build command with original arguments preserved
        cmd = [sys.executable, 'main_single.py'] + self.original_args
        
        # Launch the shard process using main_single.py with preserved arguments
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        self.processes[shard_id] = process
        
        # Monitor the process output
        async def monitor_output(stream):
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode('utf-8').strip()
                if decoded:
                    print(f"[Shard {shard_id}] {decoded}")
        
        # Start monitoring tasks
        asyncio.create_task(monitor_output(process.stdout))
        asyncio.create_task(monitor_output(process.stderr))
        
        # Monitor for crashes and auto-restart if enabled
        if auto_restart:
            asyncio.create_task(self.monitor_shard(shard_id, shard_count))
        
        return process
    
    async def monitor_shard(self, shard_id: int, shard_count: int):
        """Monitor a shard and restart it if it crashes"""
        while shard_id in self.processes:
            process = self.processes.get(shard_id)
            if process:
                return_code = await process.wait()
                
                # Check if this was an intentional shutdown for restart (exit code 99)
                if return_code == 99:
                    logger.info(LogArea.STARTUP, f"Shard {shard_id} requested manager restart")
                    self.should_restart = True
                    self.restart_event.set()
                    break
                # Check if this was a normal shutdown (exit code 0)
                elif return_code == 0:
                    logger.info(LogArea.STARTUP, f"Shard {shard_id} shut down cleanly")
                    break
                
                # Shard crashed, attempt restart
                logger.warning(LogArea.STARTUP, f"Shard {shard_id} crashed with exit code {return_code}")
                
                # Check restart attempts
                restart_count = self.shard_restart_counts.get(shard_id, 0)
                
                if restart_count >= self.max_restart_attempts:
                    logger.error(LogArea.STARTUP, f"Shard {shard_id} exceeded max restart attempts ({self.max_restart_attempts})")
                    break
                
                # Wait before restarting
                logger.info(LogArea.STARTUP, f"Restarting shard {shard_id} in {self.restart_cooldown} seconds...")
                await asyncio.sleep(self.restart_cooldown)
                
                # Restart the shard
                self.shard_restart_counts[shard_id] = restart_count + 1
                logger.info(LogArea.STARTUP, f"Restarting shard {shard_id} (attempt {restart_count + 1}/{self.max_restart_attempts})")
                
                await self.launch_shard(shard_id, shard_count, auto_restart=False)
                
                # Recursively monitor the new process
                await self.monitor_shard(shard_id, shard_count)
            else:
                break
    
    
    async def _monitor_processes(self):
        """Monitor all processes until they're done"""
        while self.processes:
            await asyncio.sleep(5)
            
            # Remove finished processes
            finished_shards = []
            for shard_id, process in self.processes.items():
                if process.returncode is not None:
                    finished_shards.append(shard_id)
            
            for shard_id in finished_shards:
                del self.processes[shard_id]
                if not self.should_restart:
                    logger.info(LogArea.STARTUP, f"Shard {shard_id} has finished")
    
    async def _wait_for_restart(self):
        """Wait for restart signal"""
        await self.restart_event.wait()
    
    async def _shutdown_all_shards(self):
        """Shutdown all running shards"""
        for shard_id, process in self.processes.items():
            if process.returncode is None:
                logger.info(LogArea.STARTUP, f"Terminating shard {shard_id}...")
                process.terminate()
        
        # Wait for all to terminate
        if self.processes:
            await asyncio.gather(
                *[p.wait() for p in self.processes.values()],
                return_exceptions=True
            )
        
        self.processes.clear()
        self.shard_restart_counts.clear()
    
    async def run(self):
        """Run the shard manager"""
        try:
            # Determine shard count
            if self.shard_count is None:
                self.shard_count = await self.get_recommended_shards()
                if not self.no_shard:
                    logger.info(LogArea.STARTUP, f"Auto-detected shard count: {self.shard_count}")
            else:
                logger.info(LogArea.STARTUP, f"Using manual shard count: {self.shard_count}")
            
            # If only 1 shard needed or no-shard mode, run the bot directly
            if self.shard_count == 1 or self.no_shard:
                logger.info(LogArea.STARTUP, "Running in single-instance mode")
                
                # Build command with original arguments preserved for single-instance mode
                cmd = [sys.executable, 'main_single.py'] + self.original_args
                
                # Run as subprocess to preserve arguments on restart
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=None,  # Inherit stdout
                    stderr=None,  # Inherit stderr
                    stdin=None    # Inherit stdin
                )
                
                # Wait for process to complete
                return_code = await process.wait()
                
                # Check if bot requested restart (return code 99)
                if return_code == 99:
                    logger.info(LogArea.STARTUP, "Single instance requested restart")
                    return True  # Signal restart needed
                return False
            
            # Determine which shards to run
            if self.shard_ids is None:
                self.shard_ids = list(range(self.shard_count))
            
            logger.info(LogArea.STARTUP, f"Launching {len(self.shard_ids)} shard(s): {self.shard_ids}")
            
            # Launch all shards
            for shard_id in self.shard_ids:
                await self.launch_shard(shard_id, self.shard_count)
            
            # Monitor shards (the monitor tasks are already running)
            logger.info(LogArea.STARTUP, "All shards launched, monitoring...")
            
            # Create tasks for monitoring
            monitor_task = asyncio.create_task(self._monitor_processes())
            restart_task = asyncio.create_task(self._wait_for_restart())
            
            # Wait for either all processes to finish or restart signal
            done, pending = await asyncio.wait(
                [monitor_task, restart_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Check if we should restart
            if self.should_restart:
                logger.info(LogArea.STARTUP, "Manager restart requested, shutting down all shards...")
                await self._shutdown_all_shards()
                return True  # Signal that restart is needed
            
            logger.info(LogArea.STARTUP, "All shards have shut down")
            return False  # No restart needed
            
        except KeyboardInterrupt:
            logger.info(LogArea.STARTUP, "Received shutdown signal, stopping all shards...")
            for shard_id, process in self.processes.items():
                process.terminate()
            await asyncio.gather(*[p.wait() for p in self.processes.values()], return_exceptions=True)
        except Exception as e:
            logger.error(LogArea.STARTUP, f"Fatal error in shard manager: {e}")
            raise
        finally:
            logger.info(LogArea.STARTUP, "Shard manager shutdown complete")


async def main():
    """Main entry point with automatic sharding support and self-restart"""
    parser = argparse.ArgumentParser(description='ClearTimer Bot with automatic sharding')
    parser.add_argument('--shards', type=int, help='Total number of shards (auto-detect if not specified)')
    parser.add_argument('--shard-ids', type=str, help='Comma-separated list of shard IDs to run (all if not specified)')
    parser.add_argument('--no-shard', action='store_true', help='Run in single-instance mode without sharding')
    parser.add_argument('--force-shards', type=int, help='Force a specific number of shards (overrides auto-detection)')
    parser.add_argument('--max-restarts', type=int, default=10, help='Maximum number of restart attempts (default: 10)')
    parser.add_argument('--restart-cooldown', type=int, default=30, help='Cooldown between shard restarts in seconds (default: 30)')
    
    args = parser.parse_args()
    
    # Store original arguments to pass to child processes
    original_args = sys.argv[1:]  # Get all arguments except script name
    
    # Parse shard IDs if provided
    shard_ids = None
    if args.shard_ids:
        shard_ids = [int(x.strip()) for x in args.shard_ids.split(',')]
    
    # Use force-shards if provided, otherwise use shards
    shard_count = args.force_shards if args.force_shards else args.shards
    
    restart_count = 0
    max_restarts = args.max_restarts
    
    while True:
        try:
            # Create and run shard manager with original arguments
            manager = ShardManager(
                shard_count=shard_count, 
                shard_ids=shard_ids, 
                no_shard=args.no_shard,
                original_args=original_args
            )
            
            # Apply custom restart settings if provided
            if args.restart_cooldown:
                manager.restart_cooldown = args.restart_cooldown
            if args.max_restarts:
                manager.max_restart_attempts = args.max_restarts // 3  # Divide by 3 for per-shard attempts
            
            needs_restart = await manager.run()
            
            if needs_restart:
                restart_count += 1
                if restart_count > max_restarts:
                    logger.error(LogArea.STARTUP, f"Maximum restart attempts ({max_restarts}) exceeded")
                    break
                
                logger.info(LogArea.STARTUP, f"=== RESTARTING SHARD MANAGER (attempt {restart_count}/{max_restarts}) ===")
                await asyncio.sleep(5)  # Brief pause before restart
                continue
            else:
                # Normal shutdown, no restart needed
                break
                
        except KeyboardInterrupt:
            logger.info(LogArea.STARTUP, "Received keyboard interrupt, shutting down...")
            break
        except Exception as e:
            logger.error(LogArea.STARTUP, f"Fatal error in main loop: {e}")
            restart_count += 1
            if restart_count > max_restarts:
                logger.error(LogArea.STARTUP, f"Maximum restart attempts ({max_restarts}) exceeded after error")
                break
            logger.info(LogArea.STARTUP, f"Attempting restart after error (attempt {restart_count}/{max_restarts})...")
            await asyncio.sleep(10)  # Longer pause after error
    
    logger.info(LogArea.STARTUP, "Bot manager terminated")


if __name__ == "__main__":
    # Set up asyncio for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run the bot with automatic sharding and restart capability
    asyncio.run(main())
