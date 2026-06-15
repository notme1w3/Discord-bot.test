import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

from database import (
    init_db,
    get_user,
    update_user
)

from rank_manager import (
    RANKS,
    get_rank,
    get_next
)

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
PROMO_CHANNEL = int(os.getenv("PROMOTION_CHANNEL_ID"))
LOG_CHANNEL = int(os.getenv("XP_LOG_CHANNEL_ID"))
MANAGER_ROLE = int(os.getenv("XP_MANAGER_ROLE_ID"))

# =====================
# FLASK KEEP ALIVE
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


def is_manager(member):
    return any(r.id == MANAGER_ROLE for r in member.roles)


def embed(title, desc):
    e = discord.Embed(title=title, description=desc, color=0x2ecc71)
    e.set_footer(text="El Mancho")
    return e


# =====================
# XP LOGIC (RESET SYSTEM)
# =====================

async def add_progress(user_id, amount):
    xp, index = await get_user(user_id)

    xp += amount

    # LEVEL UP LOOP (important)
    while xp >= 100:
        xp -= 100
        index += 1

        if index >= len(RANKS):
            index = len(RANKS) - 1
            xp = 100  # maxed out

    await update_user(user_id, xp, index)

    return xp, index


async def remove_progress(user_id, amount):
    xp, index = await get_user(user_id)

    xp -= amount

    while xp < 0 and index > 0:
        index -= 1
        xp += 100

    if xp < 0:
        xp = 0

    await update_user(user_id, xp, index)

    return xp, index


async def sync_roles(member, index):
    rank = get_rank(index)
    role = member.guild.get_role(rank["role_id"])

    if not role:
        return rank

    all_ids = [r["role_id"] for r in RANKS]

    try:
        await member.remove_roles(
            *[r for r in member.roles if r.id in all_ids]
        )
    except discord.Forbidden:
        pass

    try:
        await member.add_roles(role)
    except discord.Forbidden:
        pass

    return rank


# =====================
# EVENTS
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


@bot.command()
async def addxp(ctx, member: discord.Member, amount: int, *, reason="none"):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    xp, index = await add_progress(member.id, amount)
    rank = await sync_roles(member, index)

    log_ch = bot.get_channel(LOG_CHANNEL)
    promo_ch = bot.get_channel(PROMO_CHANNEL)

    await log_ch.send(
        f"➕ {ctx.author.mention} gave {amount} XP to {member.mention} ({reason})"
    )

    await promo_ch.send(
        embed=embed(
            "XP Added",
            f"{member.mention}\nRank: {rank['name']}\nXP: {xp}/100"
        )
    )

    await ctx.send("XP added")


@bot.command()
async def removexp(ctx, member: discord.Member, amount: int, *, reason="none"):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    xp, index = await remove_progress(member.id, amount)
    rank = await sync_roles(member, index)

    log_ch = bot.get_channel(LOG_CHANNEL)

    await log_ch.send(
        f"➖ {ctx.author.mention} removed {amount} XP from {member.mention} ({reason})"
    )

    await ctx.send("XP removed")


@bot.command()
async def setxp(ctx, member: discord.Member, amount: int):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    # RESET STYLE SET
    index = 0
    while amount >= 100:
        amount -= 100
        index += 1

    await update_user(member.id, amount, index)

    await sync_roles(member, index)

    await ctx.send("XP set")


# =====================
# START
# =====================

bot.run(TOKEN)
