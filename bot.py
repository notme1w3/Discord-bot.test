import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

from database import *
from rank_manager import *

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
PROMO = int(os.getenv("PROMOTION_CHANNEL_ID"))
LOGS = int(os.getenv("XP_LOG_CHANNEL_ID"))
MANAGER = int(os.getenv("XP_MANAGER_ROLE_ID"))

# ---------------- FLASK ----------------

app = Flask("")

@app.route("/")
def home():
    return "El Mancho online"

def run():
    app.run(host="0.0.0.0", port=10000)

Thread(target=run, daemon=True).start()

# ---------------- BOT ----------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def is_manager(member):
    return any(r.id == MANAGER for r in member.roles)


def embed(title, desc):
    e = discord.Embed(title=title, description=desc, color=0x2ecc71)
    e.set_footer(text="El Mancho")
    return e


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await init_db()
    await bot.tree.sync()


# ---------------- XP COMMANDS ----------------

@bot.command()
async def addxp(ctx, member: discord.Member, amount: int, *, reason="none"):
    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    old, new = await add_xp(member.id, amount)
    await log(member.id, ctx.author.id, "ADD", amount, reason, old, new)

    rank = await sync(member, new)

    if rank:
        ch = bot.get_channel(PROMO)
        await ch.send(embed=embed("PROMOTION", f"{member.mention} → {rank['name']} ({new} XP)"))

    await ctx.send(f"Added {amount} XP")


@bot.command()
async def removexp(ctx, member: discord.Member, amount: int, *, reason="none"):
    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    old, new = await remove_xp(member.id, amount)
    await log(member.id, ctx.author.id, "REMOVE", amount, reason, old, new)
    await sync(member, new)

    await ctx.send(f"Removed {amount} XP")


@bot.command()
async def setxp(ctx, member: discord.Member, amount: int):
    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    old = await get_xp(member.id)
    await set_xp(member.id, amount)
    await log(member.id, ctx.author.id, "SET", amount, "set", old, amount)
    await sync(member, amount)

    await ctx.send("XP updated")


# ---------------- RANK ----------------

@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    xp = await get_xp(member.id)

    pct, cur, nxt, need = progress(xp)

    e = discord.Embed(
        title=f"{member.display_name}",
        description=f"""
**Rank:** {cur['name']}
**XP:** {xp}

{bar(pct)} {pct}%

**Next:** {nxt['name'] if nxt else 'MAX'}
**Needed:** {need}
""",
        color=0x2ecc71
    )

    await ctx.send(embed=e)


# ---------------- LEADERBOARD ----------------

@bot.command()
async def leaderboard(ctx):
    data = await top(10)

    desc = ""

    for i, (uid, xp) in enumerate(data, 1):
        user = await bot.fetch_user(uid)
        desc += f"{i}. {user.name} - {xp} XP\n"

    await ctx.send(embed=embed("LEADERBOARD", desc))


# ---------------- START ----------------

bot.run(TOKEN)
