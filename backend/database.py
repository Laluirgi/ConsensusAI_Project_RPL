import aiosqlite
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "consensus.db")


async def init_db():
    """Initialize the SQLite database and create tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS feedbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL CHECK(category IN ('bug', 'saran', 'lainnya')),
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'done')),
                created_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def add_feedback(category: str, message: str) -> int:
    """Add a new feedback entry. Returns the new feedback ID."""
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO feedbacks (category, message, created_at) VALUES (?, ?, ?)",
            (category, message, now)
        )
        await db.commit()
        return cursor.lastrowid


async def get_all_feedbacks(category: str = None) -> list:
    """Get all feedbacks, optionally filtered by category."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if category and category in ('bug', 'saran', 'lainnya'):
            cursor = await db.execute(
                "SELECT * FROM feedbacks WHERE category = ? ORDER BY created_at DESC",
                (category,)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM feedbacks ORDER BY created_at DESC"
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def update_feedback_status(feedback_id: int, status: str) -> bool:
    """Update the status of a feedback entry. Returns True if updated."""
    if status not in ('pending', 'in_progress', 'done'):
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE feedbacks SET status = ? WHERE id = ?",
            (status, feedback_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def delete_feedback(feedback_id: int) -> bool:
    """Delete a feedback entry. Returns True if deleted."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM feedbacks WHERE id = ?",
            (feedback_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def add_rating(chat_id: str, rating: int) -> int:
    """Add a new rating. Returns the new rating ID."""
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO ratings (chat_id, rating, created_at) VALUES (?, ?, ?)",
            (chat_id, rating, now)
        )
        await db.commit()
        return cursor.lastrowid


async def get_all_ratings() -> list:
    """Get all ratings."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM ratings ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_rating_stats() -> dict:
    """Get rating statistics."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) as total, AVG(rating) as average FROM ratings"
        )
        row = await cursor.fetchone()
        return {
            "total": row[0] or 0,
            "average": round(row[1], 1) if row[1] else 0
        }


async def get_feedback_stats() -> dict:
    """Get feedback statistics per category."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT 
                category,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done
            FROM feedbacks 
            GROUP BY category
        """)
        rows = await cursor.fetchall()
        stats = {}
        total = 0
        for row in rows:
            stats[row[0]] = {
                "count": row[1],
                "pending": row[2],
                "in_progress": row[3],
                "done": row[4]
            }
            total += row[1]
        stats["total"] = total
        return stats
