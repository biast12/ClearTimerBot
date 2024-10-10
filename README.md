# ClearTimer Bot

ClearTimer is a Discord bot designed to automatically clear messages in specified channels at regular intervals. This bot uses the Discord API and the APScheduler library to schedule and manage message deletion tasks.

## Adding the Bot to Your Server

You can add the bot to your server using [this link](https://discord.com/oauth2/authorize?client_id=1290353946308775987&permissions=76800&integration_type=0&scope=bot). Alternatively, you can self-host the bot using the guide provided below.

## Requirements

- Python 3.8+
- Discord Bot Token
- Required Python packages (listed in `requirements.txt`)

## Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/biast12/cleartimer.git
    cd cleartimer
    ```

2. **Create a virtual environment and activate it:**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```

4. **Ensure `servers.json` and `timezones.json` exist:**
    - `servers.json` should be an empty JSON object `{}` initially.
    - `timezones.json` should contain valid timezone abbreviations and their corresponding full names.

5. **Run `main.py` and set environment variables:**
    - When running the script for the first time, it will ask you to enter your Discord bot token for the `.env` file.
    - Additionally, you will be prompted to enter your `OWNER_ID` and `GUILD_ID`. These are optional but recommended if you want to use owner-only commands or test the bot in a specific server.

## Running the Bot

1. **Run the bot on Linux:**
    ```sh
    python3 main.py
    ```

2. **Run the bot on Windows:**
    ```sh
    python main.py
    ```

## Commands

### `/sub [timer] [target_channel]`
Subscribe a channel to message deletion.

- **Timer syntax:** `1d2h3m` for days, hours, and minutes or `HH:MM <timezone>` for specific times every day.
- **Example:** `/sub 24h #general` subscribes the `#general` channel to message deletion every 24 hours.

### `/unsub [target_channel]`
Unsubscribe a channel from message deletion.

- **Example:** `/unsub #general` unsubscribes the `#general` channel from message deletion.

### `/next [target_channel]`
Check when the next message clear is scheduled.

- **Example:** `/next #general` shows the next scheduled message clear time for the `#general` channel.

### `/ping`
Check the bot's latency.

- **Example:** `/ping` returns the bot's current latency.

### `/help`
Display available commands and help server link.

## Bot Owner Only Commands

### `/list`
List all servers and channels subscribed to message deletion.

### `/force_unsub [target_id]`
Force unsubscribe a server or channel from message deletion.

### `/blacklist_add [server_id]`
Blacklist a server from subscribing to message deletion.

### `/blacklist_remove [server_id]`
Remove a server from the blacklist.

### `/blacklist_list`
List all blacklisted servers.

### `/reload_commands`
Reload all commands without restarting the bot.

### `/owner_help`
Display owner-specific commands and help.

## Optimal Settings

- Ensure the bot has the necessary permissions to manage messages and read message history in the target channels.
- Use appropriate timer intervals to avoid hitting rate limits.

## Terms of Service

By using this bot, you agree to the [Terms of Service](https://biast12.info/cleartimer/termsofservice).

## Privacy Policy

Your privacy is important to us. Please review our [Privacy Policy](https://biast12.info/cleartimer/privacypolicy) for more information.

## Support

For further assistance, join our [support Discord server](https://discord.com/invite/ERFffj9Qs7).

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

---

Thank you for using ClearTimer! If you have any questions or feedback, feel free to reach out on our support server.