import discord
from discord.ext import commands

def initialize_bot():
    intents = discord.Intents.default()
    intents.messages = True  # Ensure message intents are enabled
    bot = commands.Bot(command_prefix="!", intents=intents)
    return bot