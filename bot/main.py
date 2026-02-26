import asyncio
import logging
from pathlib import Path

import asyncpg
from aiogram import Bot, Dispatcher, types

from bot.config import BOT_TOKEN, DB_DSN
from bot.nl2sql import question_to_sql
from loader.load_json import load_json

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

ROOT = Path(__file__).resolve().parent.parent
SQL_INIT = ROOT / "db" / "001_init.sql"
DATA_JSON = ROOT / "data" / "videos.json"

async def init_db() -> None:
    logging.info("init_db: waiting for postgres...")
    last_err = None
    for _ in range(60):
        try:
            conn = await asyncpg.connect(DB_DSN)
            await conn.close()
            break
        except Exception as e:
            last_err = e
            await asyncio.sleep(1)
    else:
        raise RuntimeError(f"Postgres is not reachable: {last_err}")

    conn = await asyncpg.connect(DB_DSN)
    try:
        await conn.execute(SQL_INIT.read_text(encoding="utf-8"))
        if DATA_JSON.exists():
            await load_json(conn, DATA_JSON)
    finally:
        await conn.close()

async def run_bot() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    @dp.message()
    async def handle(message: types.Message):
        try:
            question = (message.text or "").strip()
            if not question:
                await message.answer("0")
                return

            sql, _, _ = await question_to_sql(question)

            conn = await asyncpg.connect(DB_DSN)
            try:
                rows = await conn.fetch(sql)
            finally:
                await conn.close()

            if not rows:
                await message.answer("0")
                return

            if len(rows) == 1 and len(rows[0]) == 1:
                val = rows[0][0] 
                await message.answer(str(int(val) if val is not None else 0))
                return

            await message.answer("\n".join(str(dict(r)) for r in rows[:10]))

        except Exception:
            logging.exception("handle error")
            await message.answer("0")

    await dp.start_polling(bot)

async def main() -> None:
    await init_db()
    await run_bot()

if __name__ == "__main__":
    asyncio.run(main())