# ClearTimer Bot

ClearTimer is a powerful Discord bot that automatically clears messages in specified channels at scheduled intervals. Built with Discord.py and APScheduler, it provides flexible scheduling options and comprehensive server management features.

## Adding the Bot to Your Server

You can add the bot to your server using [this link](https://discord.com/oauth2/authorize?client_id=1290353946308775987&permissions=277025483776&integration_type=0&scope=bot). Alternatively, you can self-host the bot using the guide provided below.

## Features

- ⏰ **Flexible Scheduling**: Set timers using intervals (e.g., `24h`, `1d2h3m`) or specific daily times with timezone support
- 🔄 **Automatic Message Cleanup**: Reliably clears messages at scheduled intervals
- 🌍 **Timezone Support**: Schedule cleanups at specific times in any timezone
- 🛡️ **Server Blacklist System**: Prevent specific servers from using the bot
- 📊 **Comprehensive Management**: Track all subscribed channels and schedules
- 🔐 **Owner Controls**: Advanced administrative commands for bot management

## Required Permissions

### User Permissions
- **Manage Messages**: Required to use subscription commands (`/sub add`, `/sub remove`, `/sub update`, etc.)

### Bot Permissions
The bot requires the following permissions to function properly:
- **View Channel**: See and access channels
- **Send Messages**: Send messages and responses
- **Send Messages in Threads**: Send messages in thread channels
- **Read Message History**: Read past messages for clearing
- **Manage Messages**: Delete messages during clearing operations
- **Embed Links**: Display rich embeds for command responses
- **Use Application Commands**: Register and respond to slash commands

## Requirements

- Python 3.8+
- Discord Bot Token
- Required Python packages (listed in `requirements.txt`)

## Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/biast12/ClearTimerBot.git
    cd ClearTimerBot
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

4. **Set up environment variables:**
    - Copy `.env.example` to `.env`
    - Add your Discord bot token
    - Optionally add `OWNER_ID` and `GUILD_ID` for owner commands and testing

5. **Initialize the bot:**

    ```sh
    python main.py
    ```

    The bot will automatically set up required files and database on first run.

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

### Subscription Commands

All subscription-related commands are grouped under `/sub`:

#### `/sub add [timer] [target_channel] [ignored_message]`

Subscribe a channel to automatic message deletion. Requires `Manage Messages` permission.

- **Parameters:**
  - `timer`: Timer format (e.g., `24h`, `1d12h30m`, or `15:30 EST`)
  - `target_channel` (optional): Defaults to current channel if not specified
  - `ignored_message` (optional): Message ID or link to ignore during clearing
- **Timer formats:**
  - **Intervals:** `24h`, `1d`, `30m`, `1d12h30m` (combine days, hours, minutes)
  - **Daily schedule:** `15:30 EST`, `09:00 PST` (specific time with timezone)
- **Examples:**
  - `/sub add 12h` - Clear current channel every 12 hours
  - `/sub add 1d #announcements` - Clear #announcements daily
  - `/sub add 09:00 EST #general` - Clear #general every day at 9 AM EST
  - `/sub add 24h #general 123456789` - Clear #general daily, ignoring message 123456789

#### `/sub remove [target_channel]`

Unsubscribe a channel from automatic message deletion. Requires `Manage Messages` permission.

- **Parameters:**
  - `target_channel` (optional): Defaults to current channel if not specified
- **Examples:**
  - `/sub remove` - Stop clearing current channel
  - `/sub remove #general` - Stop clearing #general

#### `/sub info [target_channel]`

View detailed subscription information for a channel.

- **Parameters:**
  - `target_channel` (optional): Defaults to current channel if not specified
- **Shows:**
  - Channel status and timer configuration
  - Next scheduled clear time
  - List of ignored messages
  - Helpful tips for managing the subscription
- **Examples:**
  - `/sub info` - View info for current channel
  - `/sub info #general` - View info for #general

#### `/sub ignore [message] [target_channel]`

Toggle a message to be ignored during channel clearing. Requires `Manage Messages` permission.

- **Parameters:**
  - `message`: Message ID or Discord message link to toggle ignore status
  - `target_channel` (optional): Defaults to current channel if not specified
- **Examples:**
  - `/sub ignore 123456789` - Toggle ignore status for message in current channel
  - `/sub ignore https://discord.com/channels/.../123456789` - Toggle using message link
  - `/sub ignore 123456789 #general` - Toggle ignore status in #general

#### `/sub list`

List all active subscriptions in the current server.

- **Shows:**
  - All subscribed channels
  - Timer configuration for each channel
  - Next clear time for each channel
  - Number of ignored messages per channel
- **Example:**
  - `/sub list` - Display all active subscriptions

#### `/sub clear [target_channel]`

Manually trigger a message clear for a subscribed channel. Requires `Manage Messages` permission.

- **Parameters:**
  - `target_channel` (optional): Defaults to current channel if not specified
- **Examples:**
  - `/sub clear` - Manually clear current channel
  - `/sub clear #general` - Manually clear #general

#### `/sub skip [target_channel]`

Skip the next scheduled clear for a channel. Requires `Manage Messages` permission.

- **Parameters:**
  - `target_channel` (optional): Defaults to current channel if not specified
- **Description:**
  - Skips the next scheduled clear and reschedules to the following occurrence
  - Useful when you want to keep messages temporarily without stopping the subscription
- **Examples:**
  - `/sub skip` - Skip next clear for current channel
  - `/sub skip #general` - Skip next clear for #general

#### `/sub update [timer] [target_channel] [ignored_message]`

Update the timer for an existing subscription. Requires `Manage Messages` permission.

- **Parameters:**
  - `timer`: New timer format (e.g., `24h`, `1d12h30m`, or `15:30 EST`)
  - `target_channel` (optional): Defaults to current channel if not specified
  - `ignored_message` (optional): Message ID or link to add to ignore list
- **Description:**
  - Updates the timer while preserving existing ignored messages
  - Can optionally add a new ignored message during the update
- **Examples:**
  - `/sub update 12h` - Change current channel's timer to 12 hours
  - `/sub update 2d #general` - Change #general's timer to 2 days
  - `/sub update 09:00 PST #announcements` - Update to daily at 9 AM PST

### General Commands

#### `/ping`

Check the bot's response latency to Discord servers.

#### `/help`

Display comprehensive help information including commands, timer formats, and useful links.

### Owner Commands

<details>
<summary>Click to expand owner commands</summary>

These commands are restricted to the bot owner for administrative purposes. All owner commands are under the `/owner` group:

#### `/owner cache_stats`

View cache statistics and performance metrics.

#### `/owner stats`

Display comprehensive bot statistics including server count, user count, and resource usage.

#### `/owner list`

Display all servers and channels with active subscriptions.

#### `/owner force_unsub [target_id]`

Force unsubscribe a server or channel from message deletion.

#### `/owner blacklist_add [server_id]`

Add a server to the blacklist, preventing it from using the bot.

#### `/owner blacklist_remove [server_id]`

Remove a server from the blacklist.

#### `/owner blacklist_list`

Display all blacklisted servers.

#### `/owner reload_cache`

Reload all caches from database to sync with database changes.

#### `/owner error_lookup [error_id]`

Look up detailed information about a specific error by its ID.

#### `/owner error_delete [error_id]`

Delete a specific error from the database by its ID.

#### `/owner error_list [limit]`

List recent errors from the database (default: 10, max: 25).

#### `/owner error_clear`

Clear all errors from the database.

</details>

## Terms of Service

By using this bot, you agree to the [Terms of Service](https://biast12.info/cleartimer/termsofservice).

## Privacy Policy

Your privacy is important to us. Please review our [Privacy Policy](https://biast12.info/cleartimer/privacypolicy) for more information.

## Support

For further assistance, join our [support Discord server](https://discord.com/invite/ERFffj9Qs7).

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

- **Commands not showing**: Register the commands with `register_commands.py` / `register_commands.bat`
- **Timezone issues**: Check supported timezones in the bot's timezone configuration

---

Thank you for using ClearTimer! If you have any questions or feedback, feel free to reach out on our [support server](biast12.com/support).
