import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

from database import init_db, get_user, update_user

from rank_manager import (
    RANKS,
    get_rank,
    sync_progress,
    remove_progress
)

# =====================
# ENV
# =====================

load_dotenv()

TOKEN = os.getenv("TOKEN")

GUILD_ID = int(os.getenv("GUILD_ID"))
PROMO_CHANNEL = int(os.getenv("PROMOTION_CHANNEL_ID"))
LOG_CHANNEL = int(os.getenv("XP_LOG_CHANNEL_ID"))
MANAGER_ROLE = int(os.getenv("XP_MANAGER_ROLE_ID"))

# =====================
# FLASK KEEP ALIVE (RENDER FIX)
# =====================

app = Flask("")

@app.route("/")
def home():
    return "El Mancho online"

def run():
    app.run(host="0.0.0.0", port=10000)

Thread(target=run, daemon=True).start()

# =====================
# DISCORD BOT
# =====================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =====================
# HELPERS
# =====================

def is_manager(member: discord.Member):
    return any(r.id == MANAGER_ROLE for r in member.roles)


def embed(title, desc):
    e = discord.Embed(title=title, description=desc, color=0x2ecc71)
    e.set_footer(text="El Mancho")
    return e


# =====================
# READY EVENT
# =====================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await init_db()
    await bot.tree.sync()


# =====================
# COMMANDS
# =====================

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")


# =====================
# XP SYSTEM (FIXED)
# =====================

@bot.command()
async def addxp(ctx, member: discord.Member, amount: int, *, reason="none"):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    xp, index = await sync_progress(get_user, update_user, member.id, amount)
    rank = get_rank(index)

    log_ch = bot.get_channel(LOG_CHANNEL)
    promo_ch = bot.get_channel(PROMO_CHANNEL)

    if log_ch:
        await log_ch.send(
            f"➕ {ctx.author} gave {amount} XP to {member} | {rank['name']} ({xp}) | {reason}"
        )

    if promo_ch:
        next_req = RANKS[index + 1][0] if index + 1 < len(RANKS) else xp

        await promo_ch.send(
            embed=embed(
                "XP Added",
                f"{member.mention}\n"
                f"Rank: {rank['name']}\n"
                f"XP: {xp}/{next_req}"
            )
        )

    await ctx.send("XP added")


@bot.command()
async def removexp(ctx, member: discord.Member, amount: int, *, reason="none"):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    xp, index = await remove_progress(get_user, update_user, member.id, amount)
    rank = get_rank(index)

    log_ch = bot.get_channel(LOG_CHANNEL)

    if log_ch:
        await log_ch.send(
            f"➖ {ctx.author} removed {amount} XP from {member} | {rank['name']} ({xp}) | {reason}"
        )

    await ctx.send("XP removed")


@bot.command()
async def setxp(ctx, member: discord.Member, amount: int):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    # manual reset style
    from rank_manager import RANKS

    index = 0
    while index < len(RANKS) - 1 and amount >= RANKS[index + 1][0]:
        index += 1

    await update_user(member.id, amount, index)

    await ctx.send("XP set")


# =====================
# OPTIONAL: DEBUG COMMAND
# =====================

@bot.command()
async def rank(ctx, member: discord.Member = None):

    member = member or ctx.author

    xp, index = await get_user(member.id)
    rank = get_rank(index)

    next_req = RANKS[index + 1][0] if index + 1 < len(RANKS) else xp

    await ctx.send(
        f"{member.mention}\n"
        f"{rank['name']}\n"
        f"XP: {xp}/{next_req}"
    )


# =====================
# START BOT
# =====================

bot.run(TOKEN)
