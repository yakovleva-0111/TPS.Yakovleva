import json

from bot.llm_client import gigachat_chat_text
from bot.schema_prompt import build_system_prompt_for_nlu


async def llm_parse(question: str) -> dict:
    system = build_system_prompt_for_nlu()
    text = await gigachat_chat_text(system=system, user=question)
    return json.loads(text)
