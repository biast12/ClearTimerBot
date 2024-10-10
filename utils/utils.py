import os
import json
import pytz
from pathlib import Path
from dotenv import load_dotenv
from utils.logger import logger

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
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Load timezone abbreviations from the external file
def load_timezones():
    try:
        with open(TIMEZONE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Load the blacklist
def load_blacklist():
    try:
        with open(BLACKLIST_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save server data
def save_servers(servers):
    with open(DATA_FILE, 'w') as f:
        json.dump(servers, f, indent=4)

# Save the blacklist
def save_blacklist(blacklist):
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

def get_timezone(timezone_abbr):
    timezone_str = load_timezones().get(timezone_abbr)
    if not timezone_str:
        raise ValueError(f"Unknown timezone abbreviation: {timezone_abbr}")
    return pytz.timezone(timezone_str)
