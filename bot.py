import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import aiosqlite

from database import init_db, get_user, update_user
from rank_manager import RANKS, get_rank

# =====================
# ENV
# =====================
load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
PROMO_CHANNEL = int(os.getenv("PROMOTION_CHANNEL_ID"))
LOG_CHANNEL = int(os.getenv("XP_LOG_CHANNEL_ID"))
MANAGER_ROLE = int(os.getenv("XP_MANAGER_ROLE_ID"))

DB_PATH = "xp.db"

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
    e = discord.Embed(title=title, description=desc, color=0x2ecc71)
    e.set_footer(text="El Mancho")
    return e


# =====================
# XP SYSTEM (RESET STYLE)
# =====================
async def add_progress(user_id, amount):
    xp, index = await get_user(user_id)

    xp += amount

    while xp >= 100:
        xp -= 100
        index += 1

        if index >= len(RANKS):
            index = len(RANKS) - 1
            xp = 100
            break

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
    except:
        pass

    try:
        await member.add_roles(role)
    except:
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


# =====================
# ADD XP
# =====================
@bot.command()
async def addxp(ctx, member: discord.Member, amount: int, *, reason="none"):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    xp, index = await add_progress(member.id, amount)
    rank = await sync_roles(member, index)

    try:
        log_ch = await bot.fetch_channel(LOG_CHANNEL)
        promo_ch = await bot.fetch_channel(PROMO_CHANNEL)

        await log_ch.send(
            f"""
📜 XP HISTORY LOG
➕ Added XP
👤 Target: {member.mention}
👮 Staff: {ctx.author.mention}
💰 Amount: {amount}
📝 Reason: {reason}
"""
        )

        await promo_ch.send(
            embed=embed(
                "XP Added",
                f"{member.mention}\nRank: {rank['name']}\nXP: {xp}/100"
            )
        )
    except:
        pass

    await ctx.send("XP added")


# =====================
# REMOVE XP
# =====================
@bot.command()
async def removexp(ctx, member: discord.Member, amount: int, *, reason="none"):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    xp, index = await remove_progress(member.id, amount)
    rank = await sync_roles(member, index)

    try:
        log_ch = await bot.fetch_channel(LOG_CHANNEL)

        await log_ch.send(
            f"""
📜 XP HISTORY LOG
➖ Removed XP
👤 Target: {member.mention}
👮 Staff: {ctx.author.mention}
💰 Amount: {amount}
📝 Reason: {reason}
"""
        )
    except:
        pass

    await ctx.send("XP removed")


# =====================
# SET XP
# =====================
@bot.command()
async def setxp(ctx, member: discord.Member, amount: int):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    index = 0

    while amount >= 100:
        amount -= 100
        index += 1

    await update_user(member.id, amount, index)
    await sync_roles(member, index)

    await ctx.send("XP set")


# =====================
# RANK COMMAND
# =====================
@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author

    xp, index = await get_user(member.id)
    rank = RANKS[index]

    embed_msg = discord.Embed(
        title=f"{member.display_name}",
        description=f"""
🏆 Rank: {rank['name']}
⚡ XP: {xp}/100
📊 Level: {index}
""",
        color=0x2ecc71
    )

    await ctx.send(embed=embed_msg)


# =====================
# LEADERBOARD
# =====================
@bot.command()
async def leaderboard(ctx):

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            SELECT user_id, xp, rank_index
            FROM users
            ORDER BY rank_index DESC, xp DESC
            LIMIT 10
        """)
        rows = await cur.fetchall()

    desc = ""

    for i, (uid, xp, idx) in enumerate(rows, 1):
        try:
            user = await bot.fetch_user(uid)
            rank = RANKS[idx]["name"]
            desc += f"**{i}. {user.name}** - {rank} ({xp} XP)\n"
        except:
            continue

    embed_msg = discord.Embed(
        title="🏆 Leaderboard",
        description=desc,
        color=0x2ecc71
    )

    await ctx.send(embed=embed_msg)


# =====================
# START BOT
# =====================
bot.run(TOKEN)
