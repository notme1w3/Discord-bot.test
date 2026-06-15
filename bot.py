import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

from rank_manager import (
    init_db,
    apply_xp,
    remove_xp,
    get_rank,
    get_next
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

def run():
    app.run(host="0.0.0.0", port=10000)

Thread(target=run, daemon=True).start()

# =====================
# BOT
# =====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def is_manager(member):
    return any(r.id == MANAGER_ROLE for r in member.roles)


def embed(title, desc):
    e = discord.Embed(title=title, description=desc, color=0x2ecc71)
    return e


# =====================
# ROLE SYNC FIXED
# =====================
async def sync_roles(member, level):
    rank = get_rank(level)

    role = member.guild.get_role(rank["role_id"])
    if not role:
        return rank

    try:
        await member.add_roles(role)
    except:
        pass

    return rank


# =====================
# READY
# =====================
@bot.event
async def on_ready():
    await init_db()
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


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

    xp, level = await apply_xp(member.id, amount)
    rank = await sync_roles(member, level)

    log = bot.get_channel(LOG_CHANNEL)
    promo = bot.get_channel(PROMO_CHANNEL)

    await log.send(f"➕ {member.mention} +{amount} XP by {ctx.author.mention} ({reason})")

    await promo.send(embed=embed(
        "XP Added",
        f"{member.mention}\nRank: {rank['name']}\nXP: {xp}/{rank['xp']}"
    ))

    await ctx.send("XP added")


@bot.command()
async def removexp(ctx, member: discord.Member, amount: int, *, reason="none"):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    xp, level = await remove_xp(member.id, amount)
    rank = await sync_roles(member, level)

    log = bot.get_channel(LOG_CHANNEL)

    await log.send(f"➖ {member.mention} -{amount} XP by {ctx.author.mention} ({reason})")

    await ctx.send("XP removed")


@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author

    xp, level = await apply_xp(member.id, 0)
    rank = get_rank(level)
    nxt = get_next(level)

    msg = f"{member.mention}\n{rank['name']}\nXP: {xp}/{rank['xp']}"

    if nxt:
        msg += f"\nNext: {nxt['name']} ({nxt['xp']})"

    await ctx.send(msg)


# =====================
# RUN
# =====================
bot.run(TOKEN)
