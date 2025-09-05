# ClearTimer Bot

ClearTimer is a powerful Discord bot that automatically clears messages in specified channels at scheduled intervals. Built with Discord.py and APScheduler, it provides flexible scheduling options and comprehensive server management features.

## Adding the Bot to Your Server

You can add the bot to your server using [this link](https://discord.com/oauth2/authorize?client_id=1290353946308775987&permissions=277025483776&integration_type=0&scope=bot). Alternatively, you can self-host the bot using the guide provided below.

## Features

- ⏰ **Flexible Scheduling**: Set timers using intervals (e.g., `24h`, `1d2h3m`) or specific daily times with timezone support
- 🔄 **Automatic Message Cleanup**: Reliably clears messages at scheduled intervals
- 🌍 **Timezone Support**: Schedule cleanups at specific times in any timezone
- 🌐 **Multi-Language Support**: Automatic language detection on server join with support for multiple languages (English, Danish, and more)
- 🛡️ **Server Blacklist System**: Prevent specific servers from using the bot
- 📊 **Comprehensive Management**: Track all subscribed channels and schedules
- 🔐 **Owner Controls**: Advanced administrative commands for bot management

## Required Permissions

### User Permissions

- **Manage Messages**: Required to use subscription commands (`/subscription add`, `/subscription remove`, `/subscription list`, etc.)

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

All subscription-related commands are grouped under `/subscription`:

<details>
<summary>Click to expand subscription commands</summary>

#### `/subscription add [timer] [target_channel] [ignored_target]`

Subscribe a channel to automatic message deletion. Requires `Manage Messages` permission.

- **Parameters:**
  - `timer`: Timer format (e.g., `24h`, `1d12h30m`, or `15:30 EST`)
  - `target_channel` (optional): Channel to clear - defaults to current channel if not specified
  - `ignored_target` (optional): Message ID/link or user mention/ID to ignore during clearing
- **Timer Formats:**
  - **Intervals:** `24h`, `1d`, `30m`, `1d12h30m` (combine days, hours, minutes)
  - **Daily schedule:** `15:30 EST`, `09:00 PST` (specific time with timezone)
- **Examples:**
  - `/subscription add 12h` - Clear current channel every 12 hours
  - `/subscription add 1d #announcements` - Clear #announcements daily
  - `/subscription add 09:00 EST #general` - Clear #general every day at 9 AM EST
  - `/subscription add 24h #general 123456789` - Clear #general daily, ignoring message 123456789
  - `/subscription add 6h #general @JohnDoe` - Clear #general every 6 hours, ignoring JohnDoe's messages

#### `/subscription remove [target_channel]`

Unsubscribe a channel from automatic message deletion. Requires `Manage Messages` permission.

- **Parameters:**
  - `target_channel` (optional): Channel to unsubscribe - defaults to current channel if not specified
- **Examples:**
  - `/subscription remove` - Stop clearing current channel
  - `/subscription remove #general` - Stop clearing #general

#### `/subscription list`

List all active subscriptions in the current server.

- **Shows:**
  - All subscribed channels with their names
  - Timer configuration for each channel
  - Next clear time for each channel (with relative time)
  - Total number of ignored entities (messages + users) per channel
  - Helpful tip to use `/subscription info` for detailed channel information
- **Example:**
  - `/subscription list` - Display all active subscriptions in the server

#### `/subscription info [target_channel]`

View detailed subscription information for a channel.

- **Parameters:**
  - `target_channel` (optional): Channel to check - defaults to current channel if not specified
- **Shows:**
  - Channel mention and subscription status
  - Timer configuration (interval or daily schedule)
  - Next scheduled clear time (both absolute and relative)
  - List of ignored message IDs (first 5 + count of remaining)
  - List of ignored users with mentions (first 5 + count of remaining)
  - Available management commands for the subscription
- **Examples:**
  - `/subscription info` - View info for current channel
  - `/subscription info #general` - View info for #general

#### `/subscription update [timer] [target_channel] [ignored_target]`

Update the timer for an existing subscription. Requires `Manage Messages` permission.

- **Parameters:**
  - `timer`: New timer format (e.g., `24h`, `1d12h30m`, or `15:30 EST`)
  - `target_channel` (optional): Channel to update - defaults to current channel if not specified
  - `ignored_target` (optional): Message ID/link or user mention/ID to add to ignore list during update
- **Examples:**
  - `/subscription update 12h` - Change current channel's timer to 12 hours
  - `/subscription update 2d #general` - Change #general's timer to 2 days
  - `/subscription update 09:00 PST #announcements` - Update to daily at 9 AM PST

#### `/subscription ignore [target] [target_channel]`

Toggle a message or user to be ignored during channel clearing. Requires `Manage Messages` permission.

- **Parameters:**
  - `target`: Message ID/link or user mention/ID to toggle ignore status
  - `target_channel` (optional): Defaults to current channel if not specified
- **Supports:**
  - **Messages:** Provide message ID or Discord message link
  - **Users:** Provide user mention (@username) or user ID
- **Examples:**
  - `/subscription ignore 123456789` - Toggle ignore status for message in current channel
  - `/subscription ignore https://discord.com/channels/.../123456789` - Toggle using message link
  - `/subscription ignore @JohnDoe` - Toggle ignore status for a user's messages
  - `/subscription ignore 987654321 #general` - Toggle ignore status for user ID in #general

#### `/subscription clear [target_channel]`

Manually trigger a message clear for a subscribed channel. Requires `Manage Messages` permission.

- **Parameters:**
  - `target_channel` (optional): Channel to clear - defaults to current channel if not specified
- **Examples:**
  - `/subscription clear` - Manually clear current channel
  - `/subscription clear #general` - Manually clear #general

#### `/subscription skip [target_channel]`

Skip the next scheduled clear for a channel. Requires `Manage Messages` permission.

- **Parameters:**
  - `target_channel` (optional): Channel to skip - defaults to current channel if not specified
- **Use Cases:**
  - Important ongoing discussion that shouldn't be interrupted
  - Temporary need to preserve channel history
  - Postponing clear during special events
- **Examples:**
  - `/subscription skip` - Skip next clear for current channel
  - `/subscription skip #general` - Skip next clear for #general
  - `/subscription update 6h #general 123456789` - Update timer and add ignored message
  - `/subscription update 3h #general @JohnDoe` - Update timer and add ignored user

</details>

### General Commands

<details>
<summary>Click to expand general commands</summary>

#### `/ping`

Check the bot's response latency to Discord servers.

#### `/help`

Display comprehensive help information including commands, timer formats, and useful links.

#### Timezone Management

Commands for managing server timezone settings under `/timezone`:

- **`/timezone change [timezone]`**: Set the default timezone for your server (requires Manage Server permission)
  - Examples: `/timezone change America/New_York`, `/timezone change EST`, `/timezone change Europe/London`
- **`/timezone list`**: Display all available timezones from the configuration

#### Language Management

Commands for managing server language settings under `/language`:

- **`/language list`**: Display all available languages and the current server language
- **`/language change [language]`**: Change the language for your server (requires Manage Server permission)
  - Select from a dropdown list of available languages
  - Currently supports: English, Danish (Dansk)

</details>

### Admin Commands

<details>
<summary>Click to expand admin commands</summary>

These commands are restricted to bot administrators and the owner. All admin commands are under the `/admin` group:

#### `/admin stats [server_id]`

Display bot statistics. Without server_id shows overall stats (total servers, channels, blacklisted servers, errors). With server_id shows specific server stats including channel count, blacklist status, and error count for that server.

#### Blacklist Management

Commands for managing server blacklist under `/admin blacklist`:

- **`/admin blacklist add [server_id] [reason]`**: Add a server to the blacklist with optional reason
- **`/admin blacklist remove [server_id]`**: Remove a server from the blacklist  
- **`/admin blacklist check [server_id]`**: Check if a server is blacklisted and view details

#### Error Management

Commands for managing error logs under `/admin error`:

- **`/admin error check [error_id]`**: Check an error by its ID
- **`/admin error delete [error_id]`**: Delete a specific error from the database
- **`/admin error list [limit]`**: List recent errors (default: 10, max: 25)
- **`/admin error clear`**: Clear all errors from the database

#### Force Management

Commands for forcefully managing subscriptions under `/admin force`:

- **`/admin force remove_server [id]`**: Force remove all subscriptions for a server
- **`/admin force remove_channel [id]`**: Force remove a specific channel subscription

#### Cache Management

- **`/admin recache`**: Recache all data from database (except config/admins)

</details>

### Owner Commands

<details>
<summary>Click to expand owner commands</summary>

These commands are restricted to the bot owner only. All owner commands are under the `/owner` group:

#### Admin Management

Commands for managing bot administrators under `/owner admin`:

- **`/owner admin list`**: List all bot administrators
- **`/owner admin add [user_id]`**: Add a new bot administrator
- **`/owner admin remove [user_id]`**: Remove a bot administrator

#### Configuration Management

Commands for recaching configuration under `/owner recache`:

- **`/owner recache config`**: Recache bot configuration from database

#### Shard Management

Commands for managing bot shards under `/owner shard` (if bot is sharded):

- **`/owner shard status`**: View current shard status and statistics
- **`/owner shard reload`**: Reload all shards (restart bot)
- **`/owner shard reload [shard_id]`**: Reload a specific shard

</details>

## Terms of Service

By using this bot, you agree to the [Terms of Service](https://biast12.com/cleartimer/termsofservice).

## Privacy Policy

Your privacy is important to us. Please review our [Privacy Policy](https://biast12.com/cleartimer/privacypolicy) for more information.

## Support

For further assistance, join our [support Discord server](https://biast12.com/botsupport).

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
