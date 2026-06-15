import aiosqlite

DB = "xp.db"


async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            xp INTEGER DEFAULT 0,
            rank_index INTEGER DEFAULT 0
        )
        """)
        await db.commit()


async def ensure(user_id):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT user_id FROM users WHERE user_id=?",
            (user_id,)
        )
        if not await cur.fetchone():
            await db.execute(
                "INSERT INTO users(user_id, xp, rank_index) VALUES(?, 0, 0)",
                (user_id,)
            )
            await db.commit()


async def get_user(user_id):
    await ensure(user_id)

    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT xp, rank_index FROM users WHERE user_id=?",
            (user_id,)
        )
        row = await cur.fetchone()

        return row if row else (0, 0)


async def update_user(user_id, xp, rank_index):
    await ensure(user_id)

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "UPDATE users SET xp=?, rank_index=? WHERE user_id=?",
            (xp, rank_index, user_id)
        )
        await db.commit()
