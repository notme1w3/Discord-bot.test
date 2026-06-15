import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

from database import init_db, get_user, update_user
from rank_manager import RANKS, get_rank

# =====================
# ENV
# =====================
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


def make_embed(title, desc):
    e = discord.Embed(title=title, description=desc, color=0x2ecc71)
    e.set_footer(text="El Mancho")
    return e


# =====================
# XP CORE SYSTEM (CARRY OVER)
# =====================
async def process_xp(user_id, gained):
    xp, rank_index = await get_user(user_id)

    xp += gained

    while True:
        req, _ = RANKS[rank_index]

        if xp >= req:
            xp -= req
            rank_index += 1

            if rank_index >= len(RANKS):
                rank_index = len(RANKS) - 1
                xp = 0
                break
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

    if not role:
        return

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


# =====================
# ADD XP
# =====================
@bot.command()
async def addxp(ctx, member: discord.Member, amount: int, *, reason="none"):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    xp, rank_index = await process_xp(member.id, amount)
    await sync_roles(member, rank_index)

    try:
        log = await bot.fetch_channel(LOG_CHANNEL)
        promo = await bot.fetch_channel(PROMO_CHANNEL)

        req, name = RANKS[rank_index]

        await log.send(
            f"📜 XP LOG\n➕ {member.mention} +{amount} XP\n👮 {ctx.author.mention}\n📝 {reason}"
        )

        await promo.send(
            embed=make_embed(
                "Rank Update",
                f"{member.mention}\nRank: {name}\nXP: {xp}/{req}"
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

    xp, rank_index = await remove_xp(member.id, amount)
    await sync_roles(member, rank_index)

    try:
        log = await bot.fetch_channel(LOG_CHANNEL)

        await log.send(
            f"📜 XP LOG\n➖ {member.mention} -{amount} XP\n👮 {ctx.author.mention}\n📝 {reason}"
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

    rank_index = 0

    while rank_index < len(RANKS) - 1 and amount >= RANKS[rank_index][0]:
        rank_index += 1

    await update_user(member.id, amount, rank_index)
    await sync_roles(member, rank_index)

    await ctx.send("XP set")


# =====================
# RANK CHECK
# =====================
@bot.command()
async def rank(ctx, member: discord.Member = None):

    member = member or ctx.author
    xp, rank_index = await get_user(member.id)

    req, name = RANKS[rank_index]

    await ctx.send(
        embed=make_embed(
            member.display_name,
            f"Rank: {name}\nXP: {xp}/{req}"
        )
    )


# =====================
# LEADERBOARD
# =====================
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

    await ctx.send(embed=make_embed("Leaderboard", text))


# =====================
# START BOT
# =====================
bot.run(TOKEN)
