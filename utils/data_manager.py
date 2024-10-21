import os
import json
import pytz
from pathlib import Path
from dotenv import load_dotenv

# First-time installation check
env_path = Path('.env')
if not env_path.is_file():
    env_path.touch()

load_dotenv(dotenv_path=env_path)

# File paths and constants
DATA_FILE = 'servers.json'
TIMEZONE_FILE = 'timezones.json'
BLACKLIST_FILE = 'blacklist.json'

# Load or initialize server data
def load_servers():
    """
    Load the server data from the JSON file.

    Returns:
        dict: The server data.
    """
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Load timezone abbreviations from the external file
def load_timezones():
    """
    Load the timezone data from the JSON file.

    Returns:
        dict: The timezone data.
    """
    try:
        with open(TIMEZONE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Load the blacklist
def load_blacklist():
    """
    Load the blacklist data from the JSON file.

    Returns:
        dict: The blacklist data.
    """
    try:
        with open(BLACKLIST_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save server data
def save_servers(servers):
    """
    Save the server data to the JSON file.

    Args:
        servers (dict): The server data to save.
    """
    with open(DATA_FILE, 'w') as f:
        json.dump(servers, f, indent=4)

# Save the blacklist
def save_blacklist(blacklist):
    """
    Save the blacklist data to the JSON file.

    Args:
        blacklist (dict): The blacklist data to save.
    """
    with open(BLACKLIST_FILE, 'w') as f:
        json.dump(blacklist, f, indent=4)

def get_env_variable(var_name, prompt_message):
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')
    value = os.getenv(var_name)
    if not value:
        value = input(prompt_message)
        os.environ[var_name] = value
        with open('.env', 'a') as f:
            f.write(f'{var_name}={value}\n')
    return value
    
def load_env_variables():
    """
    Load environment variables from a .env file.

    Returns:
        tuple: A tuple containing the TOKEN, OWNER_ID, and GUILD_ID.
    """
    TOKEN = get_env_variable('DISCORD_BOT_TOKEN', "Please enter your Discord bot token: ")
    OWNER_ID = get_env_variable('OWNER_ID', "Please enter your User ID (for owner only commands) (can leave blank): ")
    if OWNER_ID:
        OWNER_ID = int(OWNER_ID)
    GUILD_ID = get_env_variable('GUILD_ID', "Please enter your test server ID (for owner only commands) (can leave blank): ")
    if GUILD_ID:
        GUILD_ID = int(GUILD_ID)
    return TOKEN, OWNER_ID, GUILD_ID

def get_timezone(timezone_abbr):
    timezone_str = load_timezones().get(timezone_abbr)
    if not timezone_str:
        raise ValueError(f"Unknown timezone abbreviation: {timezone_abbr}")
    return pytz.timezone(timezone_str)
