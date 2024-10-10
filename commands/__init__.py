import os
import glob
import importlib

# Get all command files in the commands directory
command_files = glob.glob(os.path.join(os.path.dirname(__file__), '*.py'))
owner_command_files = glob.glob(os.path.join(os.path.dirname(__file__), 'owner', '*.py'))

# Filter out __init__.py files
command_files = [f for f in command_files if not f.endswith('__init__.py')]
owner_command_files = [f for f in owner_command_files if not f.endswith('__init__.py')]

# Import all command modules
for file in command_files + owner_command_files:
    module_name = os.path.splitext(os.path.basename(file))[0]
    if 'owner' in file:
        importlib.import_module(f'commands.owner.{module_name}')
    else:
        importlib.import_module(f'commands.{module_name}')

# Dynamically create __all__ list
__all__ = [os.path.splitext(os.path.basename(f))[0].capitalize() + 'Command' for f in command_files + owner_command_files]