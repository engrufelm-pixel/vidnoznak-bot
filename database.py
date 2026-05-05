import aiosqlite

DB = "bot.db"


async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                phone TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_info TEXT,
                data_text TEXT,
                status TEXT DEFAULT '🆕 Новая',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def save_user(uid, username, phone):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR REPLACE INTO users VALUES (?,?,?)",
            (uid, username, phone)
        )
        await db.commit()


async def save_request(uid, order_info, data_text=""):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO requests (user_id, order_info, data_text) VALUES (?,?,?)",
            (uid, order_info, data_text)
        )
        await db.commit()


async def get_all_users():
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT id, username, phone FROM users") as c:
            return await c.fetchall()


async def get_user_requests(uid):
    async with aiosqlite.connect(DB) as db:
        async with db.execute(
            "SELECT id, order_info, status, created_at FROM requests WHERE user_id=?",
            (uid,)
        ) as c:
            return await c.fetchall()


async def set_status(rid, status):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE requests SET status=? WHERE id=?", (status, rid))
        await db.commit()