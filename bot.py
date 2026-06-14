import os
import discord

from flask import Flask
from threading import Thread

from dotenv import load_dotenv

from discord.ext import commands

from database import init_db

# =========================
# LOAD ENV
# =========================

load_dotenv()

TOKEN = os.getenv("TOKEN")

GUILD_ID = int(os.getenv("GUILD_ID"))

PROMOTION_CHANNEL_ID = int(
    os.getenv("PROMOTION_CHANNEL_ID")
)

XP_LOG_CHANNEL_ID = int(
    os.getenv("XP_LOG_CHANNEL_ID")
)

XP_MANAGER_ROLE_ID = int(
    os.getenv("XP_MANAGER_ROLE_ID")
)

# =========================
# FLASK KEEP ALIVE
# =========================

app = Flask(__name__)


@app.route("/")
def home():
    return "El Mancho is online."


def run_web():

    app.run(
        host="0.0.0.0",
        port=10000
    )


def keep_alive():

    thread = Thread(
        target=run_web
    )

    thread.daemon = True

    thread.start()


# =========================
# BOT SETUP
# =========================

intents = discord.Intents.default()

intents.message_content = True

intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# =========================
# HELPERS
# =========================


def is_xp_manager(member):

    return any(
        role.id == XP_MANAGER_ROLE_ID
        for role in member.roles
    )


def cartel_embed(title, description):

    embed = discord.Embed(
        title=title,
        description=description,
        color=0x1B5E20
    )

    embed.set_footer(
        text="El Mancho"
    )

    return embed


# =========================
# EVENTS
# =========================


@bot.event
async def on_ready():

    print("----------------")

    print(f"Logged in as {bot.user}")

    print(f"Guild: {GUILD_ID}")

    await init_db()

    try:

        synced = await bot.tree.sync()

        print(
            f"Synced {len(synced)} commands"
        )

    except Exception as e:

        print(e)

    print("----------------")


# =========================
# TEST COMMANDS
# =========================


@bot.command()
async def ping(ctx):

    await ctx.send("🏓 Pong!")


@bot.tree.command(
    name="ping",
    description="Check bot status"
)
async def slash_ping(
    interaction: discord.Interaction
):

    await interaction.response.send_message(
        "🏓 Pong!"
    )


# =========================
# START BOT
# =========================

keep_alive()

bot.run(TOKEN)
