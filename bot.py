import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# =====================
# LOAD ENV
# =====================
load_dotenv()
TOKEN = os.getenv("TOKEN")

# =====================
# FLASK KEEP ALIVE (FIX RENDER)
# =====================
app = Flask('')

@app.route('/')
def home():
    return "El Mancho is alive"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# =====================
# DISCORD BOT SETUP
# =====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# =====================
# EVENTS
# =====================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Sync failed: {e}")

# =====================
# PREFIX COMMANDS
# =====================
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# =====================
# SLASH COMMANDS
# =====================
@bot.tree.command(name="ping", description="Check if bot is online")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

# =====================
# START BOT
# =====================
keep_alive()
bot.run(TOKEN)
