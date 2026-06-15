import aiosqlite

DB = "xp.db"

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            xp INTEGER,
            rank INTEGER
        )
        """)
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT xp, rank FROM users WHERE user_id=?",
            (user_id,)
        )
        row = await cur.fetchone()

        if not row:
            await db.execute(
                "INSERT INTO users (user_id, xp, rank) VALUES (?, 0, 0)",
                (user_id,)
            )
            await db.commit()
            return 0, 0

        return row[0], row[1]

async def update_user(user_id, xp, rank):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        INSERT INTO users (user_id, xp, rank)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET xp=?, rank=?
        """, (user_id, xp, rank, xp, rank))
        await db.commit()
