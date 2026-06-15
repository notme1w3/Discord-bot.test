import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import aiosqlite

from rank_manager import (
    init_db,
    apply_xp,
    remove_xp,
    get_rank,
    get_next,
    log_xp,
    DB
)

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

Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()

# =====================
# BOT SETUP
# =====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def is_manager(member):
    return any(r.id == MANAGER_ROLE for r in member.roles)


# =====================
# READY
# =====================
@bot.event
async def on_ready():
    await init_db()
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


# =====================
# ADD XP
# =====================
@bot.command()
async def addxp(ctx, member: discord.Member, amount: int, *, reason="none"):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    xp, level = await apply_xp(member.id, amount)
    rank = get_rank(level)

    await log_xp(member.id, ctx.author.id, amount, reason, "add")

    log = bot.get_channel(LOG_CHANNEL)
    promo = bot.get_channel(PROMO_CHANNEL)

    await log.send(f"➕ {member.mention} +{amount} XP by {ctx.author.mention} ({reason})")

    await promo.send(
        embed=discord.Embed(
            title="XP Added",
            description=f"{member.mention}\nRank: {rank['name']}\nXP: {xp}/{rank['xp']}",
            color=0x2ecc71
        )
    )

    await ctx.send("XP added")


# =====================
# REMOVE XP
# =====================
@bot.command()
async def removexp(ctx, member: discord.Member, amount: int, *, reason="none"):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    xp, level = await remove_xp(member.id, amount)
    rank = get_rank(level)

    await log_xp(member.id, ctx.author.id, amount, reason, "remove")

    log = bot.get_channel(LOG_CHANNEL)

    await log.send(f"➖ {member.mention} -{amount} XP by {ctx.author.mention} ({reason})")

    await ctx.send("XP removed")


# =====================
# RANK COMMAND (UI)
# =====================
@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author

    xp, level = await apply_xp(member.id, 0)
    rank = get_rank(level)
    nxt = get_next(level)

    needed = rank["xp"]
    percent = int((xp / needed) * 100) if needed else 100

    bar = "█" * (percent // 10) + "░" * (10 - (percent // 10))

    async with aiosqlite.connect(DB) as db:
        async with db.execute("""
            SELECT action, staff_id, amount, reason
            FROM xp_history
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT 1
        """, (member.id,)) as cur:
            last = await cur.fetchone()

    history = "No history yet"

    if last:
        action, staff, amount, reason = last
        emoji = "➕" if action == "add" else "➖"

        history = f"""
{emoji} {action}
👤 Target: {member.mention}
👮 Staff: <@{staff}>
💰 Amount: {amount}
📝 Reason: {reason}
"""

    await ctx.send(f"""
**Rank:** {rank['name']}
**XP:** {xp}/{needed}

{bar} {percent}%

**Next:** {nxt['name'] if nxt else "MAX"}
**Needed:** {nxt['xp'] if nxt else "MAX"}

📜 XP HISTORY LOG
{history}
""")


# =====================
# LEADERBOARD
# =====================
@bot.command()
async def leaderboard(ctx):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("""
            SELECT user_id, xp, level FROM users
            ORDER BY level DESC, xp DESC
            LIMIT 10
        """) as cur:
            rows = await cur.fetchall()

    msg = "**🏆 LEADERBOARD**\n\n"

    for i, (uid, xp, lvl) in enumerate(rows, 1):
        msg += f"{i}. <@{uid}> - Level {lvl} ({xp} XP)\n"

    await ctx.send(msg)


# =====================
# RUN
# =====================
bot.run(TOKEN)
