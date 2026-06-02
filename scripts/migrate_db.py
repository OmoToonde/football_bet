"""
DB migration script — adds columns that didn't exist in the initial schema.
Safe to re-run (catches 'duplicate column' errors).

Usage:  python -m scripts.migrate_db
"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.database import engine

MIGRATIONS = [
    # Milestone 5: structured explanation JSON
    "ALTER TABLE predictions ADD COLUMN explanation_json TEXT",
]


async def run():
    async with engine.begin() as conn:
        for sql in MIGRATIONS:
            try:
                await conn.execute(__import__("sqlalchemy").text(sql))
                print(f"  OK  {sql}")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print(f"  --  already exists: {sql.split('ADD COLUMN')[1].strip()}")
                else:
                    print(f"  !!  {e}")
    print("Migration complete.")


if __name__ == "__main__":
    asyncio.run(run())
