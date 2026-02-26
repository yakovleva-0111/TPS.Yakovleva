import json
import re

from bot.schema_prompt import build_system_prompt_for_nlu
from bot.llm_client import gigachat_chat_text


MONTH_PATTERNS = [
    r"январ[ьяе]?", r"феврал[ьяе]?", r"март[ае]?", r"апрел[ьяе]?",
    r"май|мая|мае", r"июн[ьяе]?", r"июл[ьяе]?", r"август[ае]?",
    r"сентябр[ьяе]?", r"октябр[ьяе]?", r"ноябр[ьяе]?", r"декабр[ьяе]?",
]


def _extract_json(text: str) -> dict:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise ValueError("No JSON found in model output")
        return json.loads(m.group(0))


def _question_has_month(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(rf"\b{p}\b", t) for p in MONTH_PATTERNS)


def _extract_month_yyyy_mm(question: str) -> str | None:
    t = (question or "").lower()
    year_m = re.search(r"\b(\d{4})\b", t)
    if not year_m:
        return None
    year = int(year_m.group(1))

    month_num = None
    mapping = [
        (r"январ[ьяе]?", 1),
        (r"феврал[ьяе]?", 2),
        (r"март[ае]?", 3),
        (r"апрел[ьяе]?", 4),
        (r"май|мая|мае", 5),
        (r"июн[ьяе]?", 6),
        (r"июл[ьяе]?", 7),
        (r"август[ае]?", 8),
        (r"сентябр[ьяе]?", 9),
        (r"октябр[ьяе]?", 10),
        (r"ноябр[ьяе]?", 11),
        (r"декабр[ьяе]?", 12),
    ]
    for pat, mon in mapping:
        if re.search(rf"\b{pat}\b", t):
            month_num = mon
            break

    if month_num is None:
        return None

    return f"{year:04d}-{month_num:02d}"


async def llm_parse(question: str) -> dict:
    system = build_system_prompt_for_nlu()
    raw = await gigachat_chat_text(system=system, user=question)
    data = _extract_json(raw)

    q = (question or "").lower()

    m_hours = re.search(r"первые\s+(\d+)\s+час", q)
    if "после публикац" in q and "прирост" in q:
        hours = int(m_hours.group(1)) if m_hours else 3

        if "коммент" in q:
            metric = "comments"
        elif "лайк" in q:
            metric = "likes"
        elif "просмотр" in q:
            metric = "views"
        elif "репорт" in q or "жалоб" in q:
            metric = "reports"
        else:
            metric = None

        if metric:
             return {
                "intent": "total_delta_first_hours_after_publish",
                "metric": metric,
                "threshold": None,
                "creator_id": None,
                "date_from": None,
                "date_to": None,
                "month": None,
                "day": None,
                "hours": hours,
            }

    if "прирост" in q and _question_has_month(q) and re.search(r"\b\d{4}\b", q):
        if "лайк" in q:
            metric = "likes"
        elif "просмотр" in q:
            metric = "views"
        elif "коммент" in q:
            metric = "comments"
        elif "репорт" in q or "жалоб" in q:
            metric = "reports"
        else:
            metric = None

        month_fixed = _extract_month_yyyy_mm(question)
        if metric and month_fixed:
            return {
                "intent": "total_delta_in_month",
                "metric": metric,
                "threshold": None,
                "creator_id": None,
                "date_from": None,
                "date_to": None,
                "month": month_fixed,
                "day": None,
            }

    if ("опублик" in q or "опубликован" in q) and ("видео" in q) and _question_has_month(q):
        if "просмотр" in q:
            metric = "views"
        elif "лайк" in q:
            metric = "likes"
        elif "коммент" in q:
            metric = "comments"
        elif "репорт" in q or "жалоб" in q:
            metric = "reports"
        else:
            metric = None

        month_fixed = _extract_month_yyyy_mm(question)
        if metric and month_fixed:
            data = {
                "intent": "total_metric_sum_in_month",
                "metric": metric,
                "threshold": None,
                "creator_id": None,
                "date_from": None,
                "date_to": None,
                "month": month_fixed,
                "day": None,
            }
            return data

    m = re.search(r"id\s+([0-9a-f]{32})", q)
    t = re.search(r"больше\s+([\d\s]+)", q)

    if ("креатор" in q or "креатора" in q) and m and t and "видео" in q:
        creator_id = m.group(1)
        threshold = int(t.group(1).replace(" ", ""))

        if "просмотр" in q:
            metric = "views"
        elif "лайк" in q:
            metric = "likes"
        elif "коммент" in q:
            metric = "comments"
        elif "репорт" in q or "жалоб" in q:
            metric = "reports"
        else:
            metric = None

        if metric:
            data = {
                "intent": "creator_videos_over_threshold",
                "metric": metric,
                "threshold": threshold,
                "creator_id": creator_id,
                "date_from": None,
                "date_to": None,
                "month": None,
                "day": None,
            }
            return data
        
    q = (question or "").lower()

    if ("прирост" in q) and _question_has_month(q) and ("за" in q) and ("год" in q or "года" in q or re.search(r"\b\d{4}\b", q)):
        if "просмотр" in q:
            metric = "views"
        elif "лайк" in q:
            metric = "likes"
        elif "коммент" in q:
            metric = "comments"
        elif "репорт" in q or "жалоб" in q:
            metric = "reports"
        else:
            metric = None

        month_fixed = _extract_month_yyyy_mm(question)
        if metric and month_fixed:
            data = {
                "intent": "total_delta_in_month",
                "metric": metric,
                "threshold": None,
                "creator_id": None,
                "date_from": None,
                "date_to": None,
                "month": month_fixed,
                "day": None,
            }
            return data

    if ("сколько" in q and "видео" in q and ("всего" in q or "есть" in q or "в системе" in q)) and not _question_has_month(q):
        data = {
            "intent": "total_videos",
            "metric": None,
            "threshold": None,
            "creator_id": None,
            "date_from": None,
            "date_to": None,
            "month": None,
            "day": None,
        }
        return data

    if data.get("intent") == "total_videos_in_month":
        month = data.get("month")
        if not month or not re.fullmatch(r"\d{4}-\d{2}", str(month)):
            data["month"] = _extract_month_yyyy_mm(question)

    return data