import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
command_prefix="!",
intents=intents,
help_command=None
)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
try:
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands")
except Exception as e:
    print(f"Sync failed: {e}")

@bot.command()
async def ping(ctx):
await ctx.send("🏓 Pong!")

@bot.tree.command(name="ping", description="Check if the bot is online")
async def slash_ping(interaction: discord.Interaction):
await interaction.response.send_message("🏓 Pong!")

bot.run(TOKEN)
