import asyncio
import logging
from pathlib import Path

import asyncpg
from aiogram import Bot, Dispatcher, types

from bot.config import BOT_TOKEN, DB_DSN, GIGACHAT_AUTH_KEY
from bot.fallback_nlu import fallback_parse
from bot.llm_nlu import llm_parse
from bot.query_builder import build_sql
from bot.sql_safety import assert_safe_select
from loader.load_json import ensure_data_loaded


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

ROOT = Path(__file__).resolve().parent.parent
SQL_INIT = ROOT / "db" / "001_init.sql"
DATA_JSON = ROOT / "data" / "videos.json"


async def init_db() -> None:
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
        await ensure_data_loaded(conn, DATA_JSON)
    finally:
        await conn.close()


async def _parse_question(question: str) -> dict:
    if GIGACHAT_AUTH_KEY:
        try:
            return await asyncio.wait_for(llm_parse(question), timeout=8)
        except Exception:
            return fallback_parse(question)
    return fallback_parse(question)


async def run_bot() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is empty")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    @dp.message()
    async def handle(message: types.Message):
        question = (message.text or "").strip()
        if not question:
            await message.answer("0")
            return

        try:
            parsed = await _parse_question(question)
            sql, args = build_sql(parsed)
            sql = assert_safe_select(sql)

            conn = await asyncpg.connect(DB_DSN)
            try:
                val = await conn.fetchval(sql, *args)
            finally:
                await conn.close()

            if val is None:
                await message.answer("0")
            else:
                await message.answer(str(int(val)))
        except Exception:
            await message.answer("0")

    await dp.start_polling(bot)


async def main() -> None:
    await init_db()
    await run_bot()


if __name__ == "__main__":
    asyncio.run(main())
