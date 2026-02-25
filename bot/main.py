import asyncio
import logging
from pathlib import Path

import asyncpg
from aiogram import Bot, Dispatcher, types

from bot.config import BOT_TOKEN, DB_DSN
from bot.nlu import parse
from bot.sql_builder import build
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
            logging.info("init_db: postgres is reachable")
            break
        except Exception as e:
            last_err = e
            await asyncio.sleep(1)
    else:
        raise RuntimeError(f"Postgres is not reachable: {last_err}")

    conn = await asyncpg.connect(DB_DSN)
    try:
        logging.info("init_db: applying schema from %s", SQL_INIT)
        sql_text = SQL_INIT.read_text(encoding="utf-8")
        await conn.execute(sql_text)

        if DATA_JSON.exists():
            logging.info("init_db: loading JSON %s", DATA_JSON)
            await load_json(conn, DATA_JSON)
            logging.info("init_db: JSON loaded")
        else:
            logging.warning("init_db: %s not found, skipping load", DATA_JSON)
    finally:
        await conn.close()


async def run_bot() -> None:
    logging.info("bot: starting...")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    @dp.message()
    async def handle(message: types.Message):
        try:
            q = parse(message.text or "")
            sql, args = build(q)

            conn = await asyncpg.connect(DB_DSN)
            try:
                val = await conn.fetchval(sql, *args)
            finally:
                await conn.close()

            await message.answer(str(int(val) if val is not None else 0))
        except Exception as e:
            logging.exception("handle error: %s", e)
            await message.answer("0")

    logging.info("bot: polling started")
    await dp.start_polling(bot)


async def main() -> None:
    await init_db()
    await run_bot()


if __name__ == "__main__":
    asyncio.run(main())