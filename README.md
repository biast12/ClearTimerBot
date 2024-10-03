# ClearTimer Bot

ClearTimer is a Discord bot designed to automatically clear messages in specified channels at regular intervals. This bot uses the Discord API and the APScheduler library to schedule and manage message deletion tasks.

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

4. **Set up your environment variables:**
    - Create a `.env` file in the root directory of the project.
    - Add your Discord bot token to the `.env` file:
      ```env
      DISCORD_BOT_TOKEN=your_discord_bot_token
      ```

5. **Ensure `data.json` and `timezone_abbreviations.json` exist:**
    - `data.json` should be an empty JSON object `{}` initially.
    - `timezone_abbreviations.json` should contain valid timezone abbreviations and their corresponding full names.

## Running the Bot

1. **Run the bot on Linux:**
    ```sh
    python3 cleartimer.py
    ```

2. **Run the bot on Windows:**
    ```sh
    python cleartimer.py
    ```

## Commands

### `/cleartimer_sub [timer] [target_channel]`
Subscribe a channel to message deletion.

- **Timer syntax:** `1d2h3m` for days, hours, and minutes or `HH:MM <timezone>` for specific times every day.
- **Example:** `/cleartimer_sub 24h #general` subscribes the `#general` channel to message deletion every 24 hours.

### `/cleartimer_unsub [target_channel]`
Unsubscribe a channel from message deletion.

- **Example:** `/cleartimer_unsub #general` unsubscribes the `#general` channel from message deletion.

### `/cleartimer_next [target_channel]`
Check when the next message clear is scheduled.

- **Example:** `/cleartimer_next #general` shows the next scheduled message clear time for the `#general` channel.

### `/help`
Display available commands and help server link.

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