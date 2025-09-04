#!/usr/bin/env python3
"""
ClearTimer Bot - A Discord bot for automatic message clearing
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional, Dict, List
import argparse

sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import ConfigManager  # noqa: E402
from src.utils.logger import logger, LogArea  # noqa: E402


class ShardManager:
    """Manages bot sharding"""
    
    def __init__(self, shard_count: Optional[int] = None, shard_ids: Optional[List[int]] = None, original_args: Optional[List[str]] = None) -> None:
        """
        Initialize the shard manager
        
        Args:
            shard_count: Total number of shards (None for auto-detection)
            shard_ids: List of shard IDs to run on this process (None for all)
            original_args: Original command-line arguments to preserve on restart
        """
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.shard_count = shard_count
        self.shard_ids = shard_ids
        self.original_args = original_args or []
        self.processes: Dict[int, asyncio.subprocess.Process] = {}
        self.shard_restart_counts: Dict[int, int] = {}
        self.max_restart_attempts = 3
        self.restart_cooldown = 30  # seconds
        self.should_restart = False
        self.restart_event = asyncio.Event()
    
    async def get_recommended_shards(self) -> int:
        try:
            token = self.config.token
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bot {token}"
                }
                async with session.get("https://discord.com/api/v10/gateway/bot", headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        shard_count = data.get('shards', 1)
                        logger.info(LogArea.STARTUP, f"Discord recommends {shard_count} shard(s)")
                        return shard_count
                    else:
                        logger.warning(LogArea.STARTUP, f"Failed to get shard recommendation: HTTP {resp.status}")
                        return 1
            
        except Exception as e:
            logger.error(LogArea.STARTUP, f"Failed to get recommended shard count: {e}")
            return 1
    
    async def launch_shard(self, shard_id: int, shard_count: int, auto_restart: bool = True) -> 'asyncio.subprocess.Process':
        logger.info(LogArea.STARTUP, f"Launching shard {shard_id}/{shard_count - 1}")
        
        env = os.environ.copy()
        env['SHARD_ID'] = str(shard_id)
        env['SHARD_COUNT'] = str(shard_count)
        
        cmd = [sys.executable, 'shard_runner.py'] + self.original_args
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        self.processes[shard_id] = process
        
        async def monitor_output(stream) -> None:
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode('utf-8').strip()
                if decoded:
                    print(f"[Shard {shard_id}] {decoded}")
        
        asyncio.create_task(monitor_output(process.stdout))
        asyncio.create_task(monitor_output(process.stderr))
        
        if auto_restart:
            asyncio.create_task(self.monitor_shard(shard_id, shard_count))
        
        return process
    
    async def monitor_shard(self, shard_id: int, shard_count: int) -> None:
        """Monitor a shard and restart it if it crashes"""
        while shard_id in self.processes:
            process = self.processes.get(shard_id)
            if process:
                return_code = await process.wait()
                
                if return_code == 99:
                    logger.info(LogArea.STARTUP, f"Shard {shard_id} requested manager restart")
                    self.should_restart = True
                    self.restart_event.set()
                    break
                elif return_code == 0:
                    logger.info(LogArea.STARTUP, f"Shard {shard_id} shut down cleanly")
                    break
                
                logger.warning(LogArea.STARTUP, f"Shard {shard_id} crashed with exit code {return_code}")
                restart_count = self.shard_restart_counts.get(shard_id, 0)
                
                if restart_count >= self.max_restart_attempts:
                    logger.error(LogArea.STARTUP, f"Shard {shard_id} exceeded max restart attempts ({self.max_restart_attempts})")
                    break
                
                logger.info(LogArea.STARTUP, f"Restarting shard {shard_id} in {self.restart_cooldown} seconds...")
                await asyncio.sleep(self.restart_cooldown)
                self.shard_restart_counts[shard_id] = restart_count + 1
                logger.info(LogArea.STARTUP, f"Restarting shard {shard_id} (attempt {restart_count + 1}/{self.max_restart_attempts})")
                
                await self.launch_shard(shard_id, shard_count, auto_restart=False)
                
                # Recursively monitor the new process
                await self.monitor_shard(shard_id, shard_count)
            else:
                break
    
    
    async def _monitor_processes(self) -> None:
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
    
    async def _wait_for_restart(self) -> None:
        """Wait for restart signal"""
        await self.restart_event.wait()
    
    async def _shutdown_all_shards(self) -> None:
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
    
    async def run(self) -> bool:
        """Run the shard manager"""
        try:
            # Determine shard count
            if self.shard_count is None:
                self.shard_count = await self.get_recommended_shards()
                logger.info(LogArea.STARTUP, f"Auto-detected shard count: {self.shard_count}")
            else:
                logger.info(LogArea.STARTUP, f"Using manual shard count: {self.shard_count}")
            
            # Determine which shards to run
            if self.shard_ids is None:
                self.shard_ids = list(range(self.shard_count))
            
            logger.info(LogArea.STARTUP, f"Launching {len(self.shard_ids)} shard(s): {self.shard_ids}")
            
            # Launch all shards
            for shard_id in self.shard_ids:
                await self.launch_shard(shard_id, self.shard_count)
            
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
            import traceback
            logger.error(LogArea.STARTUP, f"Fatal error in shard manager: {e}")
            logger.error(LogArea.STARTUP, f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            logger.info(LogArea.STARTUP, "Shard manager shutdown complete")


async def main() -> None:
    """Main entry point with automatic sharding support and self-restart"""
    parser = argparse.ArgumentParser(description='ClearTimer Bot with automatic sharding')
    parser.add_argument('--shards', type=int, help='Total number of shards (auto-detect if not specified)')
    parser.add_argument('--shard-ids', type=str, help='Comma-separated list of shard IDs to run (all if not specified)')
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
            import traceback
            logger.error(LogArea.STARTUP, f"Fatal error in main loop: {e}")
            logger.error(LogArea.STARTUP, f"Traceback: {traceback.format_exc()}")
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
        # Use ProactorEventLoop for subprocess support on Windows
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Run the bot with automatic sharding and restart capability
    asyncio.run(main())
