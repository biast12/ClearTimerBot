import requests
import re
from utils.logger import logger

# Check if there is a new version of the app available on GitHub.
def check_for_update(current_version):
    raw_url = "https://raw.githubusercontent.com/biast12/ClearTimerBot/main/main.py"
    
    try:
        response = requests.get(raw_url)
        response.raise_for_status()
        content = response.text

        version_match = re.search(r'current_version\s*=\s*"(\d+\.\d+\.\d+)"', content)
        
        if version_match:
            latest_version = version_match.group(1)
            if latest_version > current_version:
                logger.warning(f"A new version ({latest_version}) is available! Check it out here: https://github.com/biast12/ClearTimerBot")
        else:
            logger.error("Version information not found in the main script.")
            return False
    except requests.RequestException as e:
        logger.error(f"Error checking for update: {e}")
        return False