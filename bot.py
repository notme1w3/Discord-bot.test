import os
import discord
import sqlite3
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
# SQLITE (PERSISTENT XP)
# =====================
conn = sqlite3.connect("xp.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER,
    rank INTEGER
)
""")
conn.commit()

def get_user(user_id):
    cursor.execute("SELECT xp, rank FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()

    if not data:
        cursor.execute("INSERT INTO users VALUES (?, 0, 0)", (user_id,))
        conn.commit()
        return {"xp": 0, "rank": 0}

    return {"xp": data[0], "rank": data[1]}

def save_user(user_id, xp, rank):
    cursor.execute("""
    INSERT INTO users (user_id, xp, rank)
    VALUES (?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET xp=?, rank=?
    """, (user_id, xp, rank, xp, rank))
    conn.commit()

# =====================
# RANK SYSTEM (YOUR LIST)
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

def calculate_rank(xp):
    rank = 0
    for i in range(len(RANKS)):
        if xp >= RANKS[i][0]:
            rank = i
    return rank

# =====================
# XP ENGINE (CRITICAL FIX)
# =====================
async def apply_xp(user_id, amount):
    user = get_user(user_id)

    user["xp"] += amount

    # MULTI LEVEL CARRY SYSTEM
    while True:
        if user["rank"] + 1 >= len(RANKS):
            break

        next_required = RANKS[user["rank"] + 1][0]

        if user["xp"] >= next_required:
            user["rank"] += 1
        else:
            break

    save_user(user_id, user["xp"], user["rank"])
    return user

# =====================
# CARTEL RANK CARD
# =====================
def generate_card(member, xp, rank_name, next_needed):
    img = Image.new("RGB", (900, 300), (15, 15, 15))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    draw.text((30, 30), f"{member.name}", fill="white", font=font)
    draw.text((30, 70), f"Rank: {rank_name}", fill="green", font=font)
    draw.text((30, 110), f"XP: {xp}/{next_needed}", fill="white", font=font)

    progress = min(xp / next_needed, 1) if next_needed else 1

    draw.rectangle([30, 160, 800, 190], outline="white")
    draw.rectangle([30, 160, 30 + int(770 * progress), 190], fill="green")

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
# COMMANDS
# =====================

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# ---------------- XP ADD ----------------
@bot.command()
async def addxp(ctx, member: discord.Member, amount: int, *, reason="none"):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    user = await apply_xp(member.id, amount)

    rank_name = RANKS[user["rank"]][1]
    next_needed = RANKS[user["rank"] + 1][0] if user["rank"] + 1 < len(RANKS) else user["xp"]

    log = bot.get_channel(LOG_CHANNEL)
    promo = bot.get_channel(PROMO_CHANNEL)

    await log.send(
        f"➕ XP ADDED\n👤 {member.mention}\n👮 {ctx.author.mention}\n💰 {amount}\n📝 {reason}"
    )

    card = generate_card(member, user["xp"], rank_name, next_needed)
    await promo.send(file=discord.File(card, "rank.png"))

    await ctx.send("XP added ✔")

# ---------------- REMOVE XP ----------------
@bot.command()
async def removexp(ctx, member: discord.Member, amount: int, *, reason="none"):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    user = get_user(member.id)
    user["xp"] = max(0, user["xp"] - amount)
    user["rank"] = calculate_rank(user["xp"])
    save_user(member.id, user["xp"], user["rank"])

    await ctx.send("XP removed ✔")

# ---------------- SET XP ----------------
@bot.command()
async def setxp(ctx, member: discord.Member, amount: int):

    if not is_manager(ctx.author):
        return await ctx.send("No permission")

    rank = calculate_rank(amount)
    save_user(member.id, amount, rank)

    await ctx.send("XP set ✔")

# ---------------- RANK ----------------
@bot.command()
async def rank(ctx, member: discord.Member = None):

    member = member or ctx.author
    user = get_user(member.id)

    rank_name = RANKS[user["rank"]][1]

    next_needed = (
        RANKS[user["rank"] + 1][0]
        if user["rank"] + 1 < len(RANKS)
        else user["xp"]
    )

    await ctx.send(
        f"**Rank:** {rank_name}\n"
        f"**XP:** {user['xp']}/{next_needed}"
    )

# ---------------- LEADERBOARD ----------------
@bot.command()
async def leaderboard(ctx):

    cursor.execute("SELECT user_id, xp FROM users ORDER BY xp DESC LIMIT 10")
    rows = cursor.fetchall()

    msg = "**LEADERBOARD**\n"

    for i, (uid, xp) in enumerate(rows):
        member = ctx.guild.get_member(uid)
        name = member.name if member else "Unknown"
        msg += f"{i+1}. {name} - {xp} XP\n"

    await ctx.send(msg)

# =====================
# START
# =====================
bot.run(TOKEN)
