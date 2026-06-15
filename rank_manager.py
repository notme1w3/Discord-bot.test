import aiosqlite

DB = "xp.db"

# =====================
# RANK SYSTEM (YOUR LIST)
# =====================
RANKS = [
    {"name": "Miembro", "xp": 100, "role_id": 0},
    {"name": "Miembro Respetado", "xp": 250, "role_id": 0},
    {"name": "Halconcillo", "xp": 500, "role_id": 0},
    {"name": "Pistolero", "xp": 750, "role_id": 0},
    {"name": "Asesino", "xp": 850, "role_id": 0},
    {"name": "Soldado", "xp": 950, "role_id": 0},
    {"name": "Reclutador", "xp": 1000, "role_id": 0},
    {"name": "Sicario", "xp": 1300, "role_id": 0},
    {"name": "Chofer", "xp": 1750, "role_id": 0},
    {"name": "Teniente", "xp": 2500, "role_id": 0},
    {"name": "Jefe de Plaza", "xp": 3000, "role_id": 0},
    {"name": "Comandante", "xp": 3500, "role_id": 0},
]

# =====================
# DB INIT
# =====================
async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 0
        )
        """)
        await db.commit()

# =====================
# GET USER
# =====================
async def get_user(user_id):
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            "SELECT xp, level FROM users WHERE user_id=?",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()

        if not row:
            await db.execute(
                "INSERT INTO users (user_id, xp, level) VALUES (?, 0, 0)",
                (user_id,)
            )
            await db.commit()
            return 0, 0

        return row[0], row[1]

# =====================
# UPDATE USER
# =====================
async def update_user(user_id, xp, level):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        INSERT INTO users (user_id, xp, level)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            xp=excluded.xp,
            level=excluded.level
        """, (user_id, xp, level))
        await db.commit()

# =====================
# CORE XP ENGINE (FIXED)
# =====================
async def apply_xp(user_id, amount):
    xp, level = await get_user(user_id)

    xp += amount

    # IMPORTANT: carry-over level system
    while level < len(RANKS) - 1 and xp >= RANKS[level]["xp"]:
        xp -= RANKS[level]["xp"]
        level += 1

    await update_user(user_id, xp, level)
    return xp, level

async def remove_xp(user_id, amount):
    xp, level = await get_user(user_id)

    xp -= amount

    while xp < 0 and level > 0:
        level -= 1
        xp += RANKS[level]["xp"]

    if xp < 0:
        xp = 0

    await update_user(user_id, xp, level)
    return xp, level


def get_rank(level):
    if level >= len(RANKS):
        level = len(RANKS) - 1
    return RANKS[level]


def get_next(level):
    if level + 1 >= len(RANKS):
        return None
    return RANKS[level + 1]
