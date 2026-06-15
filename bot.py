import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

from database import init_db, get_user, update_user
from rank_manager import RANKS

# =====================
# ENV
# =====================
load_dotenv()

TOKEN = os.getenv("TOKEN")
LOG_CHANNEL = int(os.getenv("XP_LOG_CHANNEL_ID"))
PROMO_CHANNEL = int(os.getenv("PROMOTION_CHANNEL_ID"))
MANAGER_ROLE = int(os.getenv("XP_MANAGER_ROLE_ID"))

# =====================
# KEEP ALIVE FLASK
# =====================
app = Flask("")

@app.route("/")
def home():
    return "El Mancho v1 online"

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
    e = discord.Embed(title=title, description=desc, color=0x2ecc71)
    e.set_footer(text="El Mancho")
    return e


# =====================
# XP SYSTEM (CARRY OVER FIXED)
# =====================
async def add_xp(user_id, amount):
    xp, rank_index = await get_user(user_id)

    xp += amount

    while rank_index < len(RANKS) - 1:
        required_xp, _ = RANKS[rank_index + 1]

        if xp >= required_xp:
            rank_index += 1
        else:
            break

    await update_user(user_id, xp, rank_index)
    return xp, rank_index


async def remove_xp(user_id, amount):
    xp, rank_index = await get_user(user_id)

    xp -= amount

    while xp < 0 and rank_index > 0:
        rank_index -= 1
        req, _ = RANKS[rank_index]
        xp += req

    if xp < 0:
        xp = 0

    await update_user(user_id, xp, rank_index)
    return xp, rank_index


# =====================
# ROLE SYNC
# =====================
async def sync_roles(member, rank_index):
    _, role_id = RANKS[rank_index]
    role = member.guild.get_role(role_id)

    if role:
        try:
            await member.add_roles(role)
        except:
            pass


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

    xp, rank_index = await add_xp(member.id, amount)
    await sync_roles(member, rank_index)

    log = bot.get_channel(LOG_CHANNEL)
    promo = bot.get_channel(PROMO_CHANNEL)

    if log:
        await log.send(f"➕ {member.mention} +{amount} XP | by {ctx.author.mention} | {reason}")

    if promo:
        req, name = RANKS[rank_index]
        await promo.send(embed=embed("Rank Update", f"{member.mention}\n{name}\nXP: {xp}/{req}"))

    await ctx.send("XP added")


@bot.command()
async def removexp(ctx, member: discord.Member, amount: int, *, reason="none"):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    xp, rank_index = await remove_xp(member.id, amount)
    await sync_roles(member, rank_index)

    log = bot.get_channel(LOG_CHANNEL)

    if log:
        await log.send(f"➖ {member.mention} -{amount} XP | by {ctx.author.mention} | {reason}")

    await ctx.send("XP removed")


@bot.command()
async def setxp(ctx, member: discord.Member, amount: int):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    rank_index = 0

    while rank_index < len(RANKS) - 1 and amount >= RANKS[rank_index + 1][0]:
        rank_index += 1

    await update_user(member.id, amount, rank_index)
    await sync_roles(member, rank_index)

    await ctx.send("XP set")


@bot.command()
async def rank(ctx, member: discord.Member = None):

    member = member or ctx.author
    xp, rank_index = await get_user(member.id)

    req, name = RANKS[rank_index]

    await ctx.send(embed=embed("Rank", f"{member.mention}\n{name}\nXP: {xp}/{req}"))


@bot.command()
async def leaderboard(ctx):
    import aiosqlite

    async with aiosqlite.connect("xp.db") as db:
        cur = await db.execute("""
            SELECT user_id, xp, rank_index
            FROM users
            ORDER BY rank_index DESC, xp DESC
            LIMIT 10
        """)
        rows = await cur.fetchall()

    text = ""

    for i, (uid, xp, idx) in enumerate(rows, 1):
        try:
            user = await bot.fetch_user(uid)
            _, name = RANKS[idx]
            text += f"{i}. {user.name} - {name} ({xp} XP)\n"
        except:
            pass

    await ctx.send(embed=embed("Leaderboard", text))


# =====================
# START BOT
# =====================
bot.run(TOKEN)
