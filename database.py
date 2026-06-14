import aiosqlite

DB_NAME = "xp.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            xp INTEGER NOT NULL DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS xp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            moderator_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            amount INTEGER NOT NULL,
            reason TEXT NOT NULL,
            old_xp INTEGER NOT NULL,
            new_xp INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await db.commit()


async def ensure_user(user_id: int):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (user_id,)
        )

        row = await cursor.fetchone()

        if row is None:

            await db.execute(
                "INSERT INTO users(user_id, xp) VALUES(?, ?)",
                (user_id, 0)
            )

            await db.commit()


async def get_xp(user_id: int):

    await ensure_user(user_id)

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            "SELECT xp FROM users WHERE user_id = ?",
            (user_id,)
        )

        row = await cursor.fetchone()

        return row[0]


async def set_xp(user_id: int, xp: int):

    await ensure_user(user_id)

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute(
            """
            UPDATE users
            SET xp = ?
            WHERE user_id = ?
            """,
            (xp, user_id)
        )

        await db.commit()


async def add_xp(user_id: int, amount: int):

    current_xp = await get_xp(user_id)

    new_xp = current_xp + amount

    await set_xp(user_id, new_xp)

    return current_xp, new_xp


async def remove_xp(user_id: int, amount: int):

    current_xp = await get_xp(user_id)

    new_xp = max(0, current_xp - amount)

    await set_xp(user_id, new_xp)

    return current_xp, new_xp


async def log_xp_change(
    user_id,
    moderator_id,
    action,
    amount,
    reason,
    old_xp,
    new_xp
):

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute(
            """
            INSERT INTO xp_logs(
                user_id,
                moderator_id,
                action,
                amount,
                reason,
                old_xp,
                new_xp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                moderator_id,
                action,
                amount,
                reason,
                old_xp,
                new_xp
            )
        )

        await db.commit()


async def get_top_users(limit=10):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            """
            SELECT user_id, xp
            FROM users
            ORDER BY xp DESC
            LIMIT ?
            """,
            (limit,)
        )

        return await cursor.fetchall()


async def get_position(user_id):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            """
            SELECT user_id, xp
            FROM users
            ORDER BY xp DESC
            """
        )

        users = await cursor.fetchall()

        for index, row in enumerate(users, start=1):

            if row[0] == user_id:
                return index

        return None
