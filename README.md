# ClearTimer Bot

> **Keep your Discord channels clean automatically** 🧹✨

ClearTimer is the ultimate solution for Discord servers that need automatic channel maintenance. Whether you're managing a gaming community, support server, or any active Discord server, ClearTimer ensures your channels stay organized without manual intervention.

## 🚀 Quick Start

**[➕ Add ClearTimer to Your Server](https://discord.com/oauth2/authorize?client_id=1290353946308775987&permissions=277025483776&integration_type=0&scope=bot)**

Just click the link above and select your server - setup takes less than a minute!

## ✨ Why ClearTimer?

### 🎯 Perfect For

- **Support Servers**: Keep ticket channels clean after resolution
- **Gaming Communities**: Clear LFG channels regularly
- **Trading Servers**: Auto-clear old trade posts
- **Event Servers**: Reset announcement channels after events
- **Learning Communities**: Clear practice/spam channels daily
- **Any Active Server**: Maintain clean, organized channels effortlessly

### 💪 Core Features

- ⏰ **Smart Scheduling**

  - Set intervals: "Clear every 6 hours" (`/subscription add 6h`)
  - Set daily times: "Clear at 3 AM EST" (`/subscription add 03:00 EST`)
  - Combine multiple timers for different channels

- 🛡️ **Intelligent Protection**

  - Preserve important messages while clearing the rest
  - Ignore specific users' messages (bots, admins, etc.)

- 🌍 **Global Timezone Support**

  - Schedule in your local timezone
  - Perfect for international communities
  - Automatic DST adjustments

- 📊 **Full Control**
  - View all active timers at a glance
  - Manually trigger clears when needed
  - Skip upcoming clears temporarily
  - Update schedules on the fly

## 📝 How to Use

### Getting Started

1. **Add the bot** using the invite link above
2. **Use** `/subscription add 24h` in any channel to clear it daily
3. **That's it!** The channel will be cleared automatically

### Example Commands

```
/subscription add 12h              # Clear this channel every 12 hours
/subscription add 09:00 PST        # Clear daily at 9 AM Pacific Time
/subscription add 24h #general     # Clear #general channel daily
/subscription list                 # See all active timers
/subscription info                 # Check current channel's timer
```

### Pro Tips

- 💡 Combine different timers for different channels
- 💡 Use `/subscription ignore @user` to preserve specific users' messages
- 💡 Set up quiet hours with timezone-specific scheduling
- 💡 Use `/subscription skip` to temporarily skip the next clear

## 🛠️ Required Permissions

ClearTimer needs these permissions to work properly:

- ✅ **Read Messages** - To see channels
- ✅ **Manage Messages** - To delete messages
- ✅ **Send Messages** - To respond to commands
- ✅ **Embed Links** - To send formatted responses
- ✅ **Use Slash Commands** - To register commands

> **Note**: Users need "Manage Messages" permission to configure timers

## 📚 Complete Command Reference

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

#### `/help`

Display comprehensive help information including commands, timer formats, and useful links.

#### `/ping`

Check the bot's response latency to Discord servers.

#### Timezone Management

Commands for managing server timezone settings under `/timezone`:

- **`/timezone list`**: Display all available timezones from the configuration
- **`/timezone change [timezone]`**: Set the default timezone for your server (requires Manage Server permission)
  - Examples: `/timezone change America/New_York`, `/timezone change EST`, `/timezone change Europe/London`

#### Language Management

Commands for managing server language settings under `/language`:

- **`/language list`**: Display all available languages and the current server language
- **`/language change [language]`**: Change the language for your server (requires Manage Server permission)
  - Select from a dropdown list of available languages
  - Currently supports: English, Danish (Dansk)

</details>

## 💙 Support & Community

- **[💬 Join Our Support Server](https://biast12.com/botsupport)** - Get help and chat with the community
- **[📝 Terms of Service](https://biast12.com/cleartimer/termsofservice)** - Usage guidelines
- **[🔒 Privacy Policy](https://biast12.com/cleartimer/privacypolicy)** - How we handle your data

---

# 🎨 Self-Hosting Guide

> **Note**: Most users should use the hosted version by [adding the bot to their server](#-quick-start). Self-hosting is for advanced users who want complete control.

## Requirements

- Python 3.8+
- Discord Bot Token
- MongoDB (local or cloud instance)
- Required Python packages (listed in `requirements.txt`)

## Prerequisites

### 1. Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Navigate to the "Bot" section
4. Create a bot and copy the token
5. Enable the following Privileged Gateway Intents:
   - Server Members Intent (required for user mentions)
   - Message Content Intent (required for message clearing)

### 2. MongoDB Setup

#### Option A: Local MongoDB Installation

1. Download and install [MongoDB Community Server](https://www.mongodb.com/try/download/community)
2. Start MongoDB service:
   - **Windows**: MongoDB should start automatically as a service
   - **Linux/Mac**: `sudo systemctl start mongod` or `brew services start mongodb-community`
3. Default connection URL: `mongodb://localhost:27017/ClearTimerBot`

#### Option B: MongoDB Atlas (Cloud)

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster (free tier available)
3. Set up database access (create a database user)
4. Add your IP address to the IP Access List
5. Get your connection string from "Connect" → "Connect your application"
6. Replace `<password>` with your database user password

## Installation

### Windows Setup

1. **Clone the repository:**

   ```cmd
   git clone https://github.com/biast12/ClearTimerBot.git
   cd ClearTimerBot
   ```

2. **Run the automated setup script:**

   ```cmd
   setup_environment.bat
   ```

   This will create a virtual environment and install all dependencies.

3. **Configure environment variables:**

   - Copy `.env.example` to `.env`
   - Edit `.env` and add your configuration:

   ```env
   # Required
   DISCORD_BOT_TOKEN=your_bot_token_here
   DATABASE_URL=mongodb://localhost:27017/ClearTimerBot  # or your MongoDB Atlas URL

   # Optional but recommended
   OWNER_ID=your_discord_user_id
   GUILD_ID=your_test_server_id
   ```

4. **Register slash commands (first time only):**

   ```cmd
   register_commands.bat
   ```

5. **Start the bot:**

   ```cmd
   start_bot.bat
   ```

### Linux/Mac Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/biast12/ClearTimerBot.git
   cd ClearTimerBot
   ```

2. **Run the automated setup script:**

   ```bash
   ./setup_environment.sh
   ```

   This will create a virtual environment and install all dependencies.

3. **Configure environment variables:**

   ```bash
   cp .env.example .env
   nano .env  # or use your preferred editor
   ```

   Add your configuration as shown in the Windows setup.

4. **Register slash commands (first time only):**

   ```bash
   ./register_commands.sh
   ```

5. **Start the bot:**

   ```bash
   ./start_bot.sh
   ```

   For sharded instances:

   ```bash
   ./start_bot.sh --shards 4
   ./start_bot.sh --shard-ids "0,1,2,3"
   ```

## Configuration Details

### Environment Variables

The bot uses the following environment variables (configured in `.env`):

#### Required Variables

- `DISCORD_BOT_TOKEN`: Your Discord bot token
- `DATABASE_URL`: MongoDB connection string

#### Optional Variables

- `OWNER_ID`: Discord user ID for owner-only commands
- `GUILD_ID`: Test server ID for development
- `APPLICATION_ID`: Discord application ID (auto-detected if not set)

#### Advanced Configuration (Optional)

```env
# Bot Branding
POWERED_BY_EMOJI_ID=1411854240443531384
POWERED_BY_EMOJI_NAME=logo
BOT_NAME=ClearTimerBot
SHOW_POWERED_BY_FOOTER=true

# Cache Configuration
CACHE_TTL_MEMORY=60
CACHE_TTL_WARM=300
CACHE_TTL_COLD=3600

# Message Settings
MISSED_CLEAR_NOTIFICATION_TIMEOUT=0.0

# Scheduler Settings
MAX_RESTART_ATTEMPTS=3
RESTART_COOLDOWN=30
CACHE_CLEANUP_INTERVAL=900

# Support Links
SUPPORT_SERVER_URL=https://biast12.com/botsupport
BOT_INVITE_URL=https://discord.com/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=277025483776&integration_type=0&scope=bot
GITHUB_URL=https://github.com/biast12/ClearTimerBot
```

### Database Structure

The bot uses MongoDB with the following collections:

- **servers**: Stores server configurations and channel subscriptions
- **blacklist**: Manages blacklisted servers
- **removed_servers**: Tracks servers the bot has left
- **errors**: Logs bot errors for debugging
- **config**: Stores bot configuration and admin users

## Running the Bot

### Development Mode

For development with auto-restart on file changes:

```bash
# Install nodemon globally (optional)
npm install -g nodemon

# Run with auto-restart
nodemon --exec python main.py
```

### Production Mode

#### Using Process Manager (PM2)

```bash
# Install PM2
npm install -g pm2

# Start the bot
pm2 start main.py --interpreter python3 --name ClearTimerBot

# Save PM2 configuration
pm2 save
pm2 startup
```

#### Using systemd (Linux)

Create `/etc/systemd/system/cleartimer.service`:

```ini
[Unit]
Description=ClearTimer Discord Bot
After=network.target mongodb.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/ClearTimerBot
Environment="PATH=/path/to/ClearTimerBot/venv/bin"
ExecStart=/path/to/ClearTimerBot/venv/bin/python /path/to/ClearTimerBot/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then enable and start:

```bash
sudo systemctl enable cleartimer
sudo systemctl start cleartimer
```

### Sharding (Large Bot Instances)

The bot supports automatic sharding for large instances:

```bash
# Auto-detect shard count
python main.py

# Manual shard configuration
python main.py --shards 4 --shard-ids 0,1,2,3

# Force specific shard count
python main.py --force-shards 8
```

## Troubleshooting

### Common Issues

#### Bot Won't Start

- **Error: "DATABASE_URL not found"**: Ensure MongoDB is running and the connection string is correct in `.env`
- **Error: "Bot token is required"**: Add your Discord bot token to `.env`
- **MongoDB connection failed**:

  - Check if MongoDB service is running
  - Verify the connection string format
  - For Atlas, ensure your IP is whitelisted

#### Commands Not Showing

- Run `register_commands.py` or `register_commands.bat` to register slash commands
- Wait 1-2 hours for global commands to propagate
- For instant testing, use guild-specific commands with `GUILD_ID` in `.env`

#### Permission Issues

- Ensure the bot has all required permissions listed in the "Bot Permissions" section
- Check that the bot role is higher than roles it needs to manage
- Verify channel-specific permissions aren't blocking the bot

#### Database Issues

- **Collections not created**: The bot creates collections automatically on first use
- **Data not persisting**: Check MongoDB logs for write errors
- **High memory usage**: Configure cache TTL values in `.env`

#### Timezone Problems

- Use `/timezone list` to see available timezones
- Ensure timezone format matches (e.g., `America/New_York`, not `EST`)
- Check pytz is installed correctly

#### Message Clearing Issues

- **Not clearing messages**: Check bot has "Manage Messages" permission
- **Skipping messages**: Some messages might be ignored (pinned, or in ignore list)
- **Rate limiting**: Discord API limits bulk delete to messages < 14 days old

### Debug Mode

Enable detailed logging by setting in `.env`:

```env
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

<div align="center">
  <h3>🎉 Thank you for using ClearTimer!</h3>
  <p>Made with ❤️ by Biast12</p>
  <p>
    <a href="https://biast12.com/botsupport">Support Server</a> •
    <a href="https://github.com/biast12/ClearTimerBot">GitHub</a> •
    <a href="https://biast12.com/cleartimer/termsofservice">Terms</a> •
    <a href="https://biast12.com/cleartimer/privacypolicy">Privacy</a>
  </p>
</div>
