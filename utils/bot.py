import discord
from discord.ext import commands

def initialize_bot():
    """
    Initialize the Discord bot with the necessary intents and command prefix.

    Returns:
        commands.Bot: The initialized bot instance.
    """
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)
    return bot