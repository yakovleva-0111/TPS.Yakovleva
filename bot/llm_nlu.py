import json
import re

from bot.schema_prompt import build_system_prompt_for_nlu
from bot.llm_client import gigachat_chat_text


MONTHS = {
    "январ": 1,
    "феврал": 2,
    "март": 3,
    "апрел": 4,
    "ма": 5,      # май/мая
    "июн": 6,
    "июл": 7,
    "август": 8,
    "сентябр": 9,
    "октябр": 10,
    "ноябр": 11,
    "декабр": 12,
}


def _extract_json(text: str) -> dict:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("No JSON found in model output")
    return json.loads(m.group(0))


def _extract_month_yyyy_mm(question: str) -> str | None:
    t = (question or "").lower()
    m = re.search(
        r"(январ[ьяе]?|феврал[ьяе]?|март[ае]?|апрел[ьяе]?|ма[йяе]?|июн[ьяе]?|июл[ьяе]?|август[ае]?|сентябр[ьяе]?|октябр[ьяе]?|ноябр[ьяе]?|декабр[ьяе]?)\s+(\d{4})",
        t,
    )
    if not m:
        return None

    mon_word = m.group(1)
    year = int(m.group(2))

    mon = None
    for k, v in MONTHS.items():
        if mon_word.startswith(k):
            mon = v
            break
    if mon is None:
        return None

    return f"{year:04d}-{mon:02d}"


async def llm_parse(question: str) -> dict:
    system = build_system_prompt_for_nlu()
    raw = await gigachat_chat_text(system=system, user=question)

    data = _extract_json(raw)

    # нормализация: если модель выбрала "за месяц", но month не заполнила
    if data.get("intent") == "total_videos_in_month":
        month = data.get("month")
        if not month or not re.fullmatch(r"\d{4}-\d{2}", str(month)):
            fixed = _extract_month_yyyy_mm(question)
            data["month"] = fixed

    return data