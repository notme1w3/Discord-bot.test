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
# KEEP ALIVE
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

def make_embed(title, desc):
    return discord.Embed(title=title, description=desc, color=0x2ecc71)

# =====================
# XP SYSTEM (FULL FIXED CARRY SYSTEM)
# =====================
async def apply_xp(user_id, amount):
    xp, rank = await get_user(user_id)

    xp += amount

    while True:
        r = get_rank(rank)

        if r["xp"] is None:
            xp = min(xp, 999999)
            break

        if xp >= r["xp"]:
            xp -= r["xp"]
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
# EVENTS
# =====================
@bot.event
async def on_ready():
    await init_db()
    print(f"Logged in as {bot.user}")

# =====================
# COMMANDS
# =====================

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# ---------------------
# ADD XP
# ---------------------
@bot.command()
async def addxp(ctx, member: discord.Member, amount: int, *, reason="none"):
    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    xp, rank = await apply_xp(member.id, amount)
    r = get_rank(rank)

    log = bot.get_channel(LOG_CHANNEL)
    promo = bot.get_channel(PROMO_CHANNEL)

    await log.send(
        f"""➕ XP LOG
Target: {member.mention}
Staff: {ctx.author.mention}
Amount: {amount}
Reason: {reason}"""
    )

    await promo.send(
        embed=make_embed(
            "XP UPDATED",
            f"{member.mention}\nRank: {r['name']}\nXP: {xp}/{r['xp'] or 'MAX'}"
        )
    )

    await ctx.send("XP added")

# ---------------------
# REMOVE XP
# ---------------------
@bot.command()
async def removexp(ctx, member: discord.Member, amount: int, *, reason="none"):
    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    xp, rank = await remove_xp(member.id, amount)
    r = get_rank(rank)

    log = bot.get_channel(LOG_CHANNEL)

    await log.send(
        f"""➖ XP LOG
Target: {member.mention}
Staff: {ctx.author.mention}
Amount: {amount}
Reason: {reason}"""
    )

    await ctx.send("XP removed")

# ---------------------
# RANK CARD (FIXED)
# ---------------------
@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author

    xp, rank_index = await get_user(member.id)
    r = get_rank(rank_index)
    nxt = get_next(rank_index)

    needed = r["xp"] or "MAX"

    percent = int((xp / r["xp"]) * 100) if r["xp"] else 100
    bar = "█" * (percent // 10) + "░" * (10 - (percent // 10))

    embed = discord.Embed(
        title="📜 CARTEL RANK",
        description=f"""
👤 {member.mention}

**Rank:** {r['name']}
**XP:** {xp}/{needed}

{bar} {percent}%

**Next:** {nxt['name'] if nxt else "MAX"}
""",
        color=0x2ecc71
    )

    await ctx.send(embed=embed)

# =====================
# START BOT
# =====================
bot.run(TOKEN)
