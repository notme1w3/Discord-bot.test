import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

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
# DISCORD SETUP
# =====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =====================
# XP / RANK SYSTEM
# =====================

RANKS = [
    (0, "Miembro"),
    (100, "Miembro Respetado"),
    (250, "Halconcillo"),
    (500, "Pistolero"),
    (750, "Asesino"),
    (850, "Soldado"),
    (950, "Reclutador"),
    (1000, "Sicario"),
    (1300, "Chofer"),
    (1750, "Teniente"),
    (2500, "Jefe de Plaza"),
    (3000, "Comandante"),
    (3500, "Salamanca Familia"),
    (4500, "Jefe de Operaciones"),
    (5500, "Mano Derecha"),
]

# in-memory storage (replace with DB later if you want persistence)
user_data = {}

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"xp": 0, "rank": 0}
    return user_data[user_id]

def get_rank(index):
    return RANKS[index]

def calculate_rank(xp):
    rank = 0
    while rank + 1 < len(RANKS) and xp >= RANKS[rank + 1][0]:
        rank += 1
    return rank

# =====================
# CORE XP ENGINE (CARRY SYSTEM FIX)
# =====================

async def apply_xp(user_id, amount):
    user = get_user(user_id)

    user["xp"] += amount

    # MULTI LEVEL UP SUPPORT
    while True:
        current_rank = user["rank"]
        if current_rank + 1 >= len(RANKS):
            break

        next_required = RANKS[current_rank + 1][0]

        if user["xp"] >= next_required:
            user["rank"] += 1
        else:
            break

    return user

# =====================
# IMAGE RANK CARD (CARTEL STYLE)
# =====================

def generate_card(member, xp, rank_name, next_rank, progress, needed):
    img = Image.new("RGB", (900, 300), (20, 20, 20))
    draw = ImageDraw.Draw(img)

    # Fonts (fallback safe)
    font = ImageFont.load_default()

    # Title
    draw.text((30, 20), f"{member.name}", fill="white", font=font)
    draw.text((30, 60), f"Rank: {rank_name}", fill="green", font=font)

    # XP
    draw.text((30, 100), f"XP: {xp}/{needed}", fill="white", font=font)

    # Progress bar
    bar_x, bar_y = 30, 160
    bar_w, bar_h = 700, 30

    draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], outline="white")

    fill = int(bar_w * progress)
    draw.rectangle([bar_x, bar_y, bar_x + fill, bar_y + bar_h], fill="green")

    # Save
    buffer = BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)
    return buffer

# =====================
# PERMISSION CHECK
# =====================

def is_manager(member):
    return any(r.id == MANAGER_ROLE for r in member.roles)

# =====================
# EMBED
# =====================

def embed(title, desc):
    e = discord.Embed(title=title, description=desc, color=0x00ff00)
    return e

# =====================
# COMMANDS
# =====================

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# ---------------------
# ADD XP (MAIN FIXED LOGIC)
# ---------------------
@bot.command()
async def addxp(ctx, member: discord.Member, amount: int, *, reason="none"):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    user = await apply_xp(member.id, amount)

    rank_name = RANKS[user["rank"]][1]
    next_needed = RANKS[user["rank"] + 1][0] if user["rank"] + 1 < len(RANKS) else user["xp"]

    progress = user["xp"] / next_needed if next_needed else 1

    log = bot.get_channel(LOG_CHANNEL)
    promo = bot.get_channel(PROMO_CHANNEL)

    await log.send(
        f"➕ XP ADDED\n"
        f"👤 {member.mention}\n"
        f"👮 {ctx.author.mention}\n"
        f"💰 {amount}\n"
        f"📝 {reason}"
    )

    card = generate_card(member, user["xp"], rank_name, "", progress, next_needed)
    file = discord.File(card, filename="rank.png")

    await promo.send(file=file)
    await ctx.send("XP added ✔")

# ---------------------
# REMOVE XP
# ---------------------
@bot.command()
async def removexp(ctx, member: discord.Member, amount: int, *, reason="none"):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    user = get_user(member.id)
    user["xp"] = max(0, user["xp"] - amount)
    user["rank"] = calculate_rank(user["xp"])

    await ctx.send("XP removed ✔")

# ---------------------
# SET XP
# ---------------------
@bot.command()
async def setxp(ctx, member: discord.Member, amount: int):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    user = get_user(member.id)
    user["xp"] = amount
    user["rank"] = calculate_rank(amount)

    await ctx.send("XP set ✔")

# ---------------------
# RANK COMMAND
# ---------------------
@bot.command()
async def rank(ctx, member: discord.Member = None):

    member = member or ctx.author
    user = get_user(member.id)

    rank_name = RANKS[user["rank"]][1]
    next_needed = RANKS[user["rank"] + 1][0] if user["rank"] + 1 < len(RANKS) else user["xp"]

    await ctx.send(
        f"**Rank:** {rank_name}\n"
        f"**XP:** {user['xp']}/{next_needed}"
    )

# ---------------------
# LEADERBOARD
# ---------------------
@bot.command()
async def leaderboard(ctx):

    top = sorted(user_data.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]

    msg = "**LEADERBOARD**\n"
    for i, (uid, data) in enumerate(top):
        member = ctx.guild.get_member(uid)
        name = member.name if member else "Unknown"
        msg += f"{i+1}. {name} - {data['xp']} XP\n"

    await ctx.send(msg)

# =====================
# START
# =====================

bot.run(TOKEN)
