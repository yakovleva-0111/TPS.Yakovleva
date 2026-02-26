from bot.schema_prompt import build_system_prompt
from bot.llm_client import gigachat_chat_json
from bot.sql_safety import assert_safe_select

async def question_to_sql(question: str) -> tuple[str, str | None, list[str]]:
    system = build_system_prompt()
    result = await gigachat_chat_json(system=system, user=question)

    sql = assert_safe_select(result.get("sql", ""))
    return sql, result.get("reason"), (result.get("assumptions") or [])