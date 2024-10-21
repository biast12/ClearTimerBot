import os
import glob
import importlib.util
from utils.logger import logger

async def load_commands(bot):
    """
    Load all command modules and add them to the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    command_files = glob.glob(os.path.join('commands', '*.py'))
    owner_command_files = glob.glob(os.path.join('commands', 'owner', '*.py'))
    all_command_files = command_files + owner_command_files

    for file in all_command_files:
        if os.path.basename(file) == '__init__.py':
            continue
        if 'owner' in file:
            extension = f"commands.owner.{os.path.splitext(os.path.basename(file))[0]}"
        else:
            extension = f"commands.{os.path.splitext(os.path.basename(file))[0]}"
        try:
            await bot.load_extension(extension)
        except Exception as e:
            logger.error(f'Failed to load extension {extension}: {e}')

def load_command_class(module_name, class_name):
    """
    Load a specific class from a module.

    Args:
        module_name (str): The name of the module.
        class_name (str): The name of the class.

    Returns:
        type: The loaded class.
    """
    module_spec = importlib.util.find_spec(module_name)
    if module_spec is None:
        raise ImportError(f"Module {module_name} not found")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    # Try different naming conventions
    possible_class_names = [
        class_name,
        class_name.capitalize() + 'Command',
        class_name.title().replace('_', '') + 'Command'
    ]
    for name in possible_class_names:
        if hasattr(module, name):
            return getattr(module, name)
    raise AttributeError(f"Module {module_name} has no attribute {class_name}")

async def sync_commands(bot):
    """
    Sync the bot's commands with Discord.

    Args:
        bot (commands.Bot): The bot instance.
    """
    try:
        # Load global commands dynamically
        command_files = glob.glob(os.path.join('commands', '*.py'))
        global_commands = [os.path.splitext(os.path.basename(file))[0] for file in command_files if os.path.basename(file) != '__init__.py']
		
        bot.tree.clear_commands(guild=None)
        for command_name in global_commands:
            command_class = load_command_class(f'commands.{command_name}', command_name)
            await bot.remove_cog(command_class)
            await bot.add_cog(command_class(bot), override=True)
        
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} commands globally')
    except Exception as e:
        logger.error(f'Failed to sync command: {e}')

async def sync_owner_commands(bot, GUILD_ID):
    """
    Sync owner-specific commands with a specific guild.

    Args:
        bot (commands.Bot): The bot instance.
        GUILD_ID (int): The ID of the guild to sync commands with.
    """
    try:
        bot_owner_guild = bot.get_guild(GUILD_ID)
        if bot_owner_guild:
            # Load owner commands dynamically
            owner_command_files = glob.glob(os.path.join('commands', 'owner', '*.py'))
            owner_commands = [os.path.splitext(os.path.basename(file))[0] for file in owner_command_files if os.path.basename(file) != '__init__.py']
			
            bot.tree.clear_commands(guild=bot_owner_guild)
            for command_name in owner_commands:
                command_class = load_command_class(f'commands.owner.{command_name}', command_name)
                await bot.remove_cog(command_class, guild=bot_owner_guild)
                await bot.add_cog(command_class(bot), guild=bot_owner_guild, override=True)
            
            synced_owner = await bot.tree.sync(guild=bot_owner_guild)
            logger.info(f'Synced {len(synced_owner)} commands for bot owner\'s guild')
    except Exception as e:
        logger.error(f'Failed to sync owner commands: {e}')