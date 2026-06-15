import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

from database import init_db, get_user, update_user
from rank_manager import RANKS, get_rank, get_next, is_max

load_dotenv()

TOKEN = os.getenv("TOKEN")
LOG_CHANNEL = int(os.getenv("XP_LOG_CHANNEL_ID"))
PROMO_CHANNEL = int(os.getenv("PROMOTION_CHANNEL_ID"))
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
# BOT SETUP
# =====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =====================
# HELPERS
# =====================

def is_manager(member):
    return any(r.id == MANAGER_ROLE for r in member.roles)

def embed(title, desc):
    return discord.Embed(title=title, description=desc, color=0x2ecc71)

# =====================
# CORE XP SYSTEM (FIXED)
# =====================

async def apply_xp(user_id, amount):
    xp, rank = await get_user(user_id)

    xp += amount

    while True:
        current_rank = get_rank(rank)

        # MAX rank
        if current_rank["xp"] is None:
            xp = min(xp, 999999)
            break

        if xp >= current_rank["xp"]:
            xp -= current_rank["xp"]
            rank += 1

            if is_max(rank):
                xp = 0
                break
        else:
            break

    await update_user(user_id, xp, rank)
    return xp, rank


async def remove_xp(user_id, amount):
    xp, rank = await get_user(user_id)

    xp -= amount

    while xp < 0 and rank > 0:
        rank -= 1
        prev = get_rank(rank)
        if prev["xp"]:
            xp += prev["xp"]
        else:
            xp = 0

    if xp < 0:
        xp = 0

    await update_user(user_id, xp, rank)
    return xp, rank


# =====================
# ROLE SYNC
# =====================

async def sync_roles(member, rank_index):
    rank = get_rank(rank_index)
    role = member.guild.get_role(rank["role_id"])

    if not role:
        return rank

    try:
        await member.remove_roles(*member.roles)
    except:
        pass

    try:
        await member.add_roles(role)
    except:
        pass

    return rank

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

    xp, rank = await apply_xp(member.id, amount)
    rank_data = get_rank(rank)

    log = bot.get_channel(LOG_CHANNEL)
    promo = bot.get_channel(PROMO_CHANNEL)

    await log.send(
        f"➕ XP Added\n"
        f"Target: {member.mention}\n"
        f"Staff: {ctx.author.mention}\n"
        f"Amount: {amount}\n"
        f"Reason: {reason}"
    )

    await promo.send(
        embed=embed(
            "XP Updated",
            f"{member.mention}\n"
            f"Rank: {rank_data['name']}\n"
            f"XP: {xp}/{rank_data['xp'] or 'MAX'}"
        )
    )

    await ctx.send("XP added")

@bot.command()
async def removexp(ctx, member: discord.Member, amount: int, *, reason="none"):
    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    xp, rank = await remove_xp(member.id, amount)
    rank_data = get_rank(rank)

    log = bot.get_channel(LOG_CHANNEL)

    await log.send(
        f"➖ XP Removed\n"
        f"Target: {member.mention}\n"
        f"Staff: {ctx.author.mention}\n"
        f"Amount: {amount}\n"
        f"Reason: {reason}"
    )

    await ctx.send("XP removed")

@bot.command()
async def setxp(ctx, member: discord.Member, amount: int):
    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    rank = 0
    xp = amount

    while True:
        r = get_rank(rank)
        if r["xp"] is None:
            break
        if xp >= r["xp"]:
            xp -= r["xp"]
            rank += 1
        else:
            break

    await update_user(member.id, xp, rank)
    await ctx.send("XP set")

# =====================
# START
# =====================

@bot.event
async def on_ready():
    await init_db()
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
