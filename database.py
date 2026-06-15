import aiosqlite

DB = "xp.db"


async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            xp INTEGER DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            moderator_id INTEGER,
            action TEXT,
            amount INTEGER,
            reason TEXT,
            old_xp INTEGER,
            new_xp INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await db.commit()


async def ensure(user_id):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT xp FROM users WHERE user_id=?",
            (user_id,)
        )
        if not await cur.fetchone():
            await db.execute(
                "INSERT INTO users(user_id, xp) VALUES(?, 0)",
                (user_id,)
            )
            await db.commit()


async def get_xp(user_id):
    await ensure(user_id)
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT xp FROM users WHERE user_id=?",
            (user_id,)
        )
        return (await cur.fetchone())[0]


async def set_xp(user_id, xp):
    await ensure(user_id)
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "UPDATE users SET xp=? WHERE user_id=?",
            (xp, user_id)
        )
        await db.commit()


async def add_xp(user_id, amount):
    old = await get_xp(user_id)
    new = old + amount
    await set_xp(user_id, new)
    return old, new


async def remove_xp(user_id, amount):
    old = await get_xp(user_id)
    new = max(0, old - amount)
    await set_xp(user_id, new)
    return old, new


async def log(user_id, mod_id, action, amount, reason, old, new):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        INSERT INTO logs (
            user_id, moderator_id, action,
            amount, reason, old_xp, new_xp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, mod_id, action,
            amount, reason, old, new
        ))
        await db.commit()


async def top(limit=10):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("""
        SELECT user_id, xp
        FROM users
        ORDER BY xp DESC
        LIMIT ?
        """, (limit,))
        return await cur.fetchall()
