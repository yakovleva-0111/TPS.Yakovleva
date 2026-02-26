import re
from datetime import date

from bot.ru_dates import parse_ru_day, parse_ru_range


_METRIC = {
    "просмотр": "views",
    "просмотров": "views",
    "лайк": "likes",
    "лайков": "likes",
    "комментар": "comments",
    "комментариев": "comments",
    "коммент": "comments",
    "комментов": "comments",
    "жалоб": "reports",
    "репорт": "reports",
    "репортов": "reports",
}

MONTHS = {
    "январ": 1, "феврал": 2, "март": 3, "апрел": 4, "ма": 5,
    "июн": 6, "июл": 7, "август": 8, "сентябр": 9, "октябр": 10,
    "ноябр": 11, "декабр": 12,
}


def _pick_metric(text: str) -> str | None:
    t = text.lower()
    for k, v in _METRIC.items():
        if k in t:
            return v
    return None


def fallback_parse(question: str) -> dict:
    q = (question or "").strip()
    t = q.lower()

    m = re.search(r"за\s+(январ[ьяе]?|феврал[ьяе]?|март[ае]?|апрел[ьяе]?|ма[йяе]?|июн[ьяе]?|июл[ьяе]?|август[ае]?|сентябр[ьяе]?|октябр[ьяе]?|ноябр[ьяе]?|декабр[ьяе]?)\s+(\d{4})", t)
    if m and ("сколько" in t and "видео" in t):
        mon_word = m.group(1)
        year = int(m.group(2))

        mon = None
        for k, v in MONTHS.items():
            if mon_word.startswith(k):
                mon = v
                break
            if mon is None:
                raise ValueError("month parse failed")

        date_from = date(year, mon, 1).isoformat()
        if mon == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, mon + 1, 1)
        date_to = (next_month).isoformat()

        return {
            "intent": "videos_in_month",
            "date_from": date_from,
            "date_to_exclusive": date_to
        }

    m = re.search(r"(общее количество|всего)\s+(лайков|просмотров|комментариев|репортов|жалоб)", t)
    if m:
        word = m.group(2)
        metric = {
            "лайков": "likes",
            "просмотров": "views",
            "комментариев": "comments",
            "репортов": "reports",
            "жалоб": "reports",
        }[word]
        return {"intent": "total_metric_sum", "metric": metric}

    if "сколько" in t and "видео" in t and "всего" in t:
        return {
            "intent": "total_videos",
            "metric": None,
            "creator_id": None,
            "threshold": None,
            "date_from": None,
            "date_to": None,
            "day": None,
        }

    if "креатора" in t and "вышло" in t:
        m = re.search(r"id\s*([0-9a-f\-]{36})", t)
        if not m:
            raise ValueError("creator id not found")
        date_from, date_to = parse_ru_range(t)
        return {
            "intent": "creator_videos_in_range",
            "metric": None,
            "creator_id": m.group(1),
            "threshold": None,
            "date_from": date_from,
            "date_to": date_to,
            "day": None,
        }

    if "больше" in t and "видео" in t:
        metric = _pick_metric(t)
        n = int(re.search(r"больше\s+(\d+)", t).group(1))
        return {
            "intent": "videos_over_threshold",
            "metric": metric or "views",
            "creator_id": None,
            "threshold": n,
            "date_from": None,
            "date_to": None,
            "day": None,
        }

    if "в сумме вырос" in t or "на сколько" in t:
        metric = _pick_metric(t) or "views"
        day = parse_ru_day(t)
        return {
            "intent": "total_delta_on_day",
            "metric": metric,
            "creator_id": None,
            "threshold": None,
            "date_from": None,
            "date_to": None,
            "day": day,
        }

    if "сколько разных" in t and "получал" in t and "нов" in t:
        metric = _pick_metric(t) or "views"
        day = parse_ru_day(t)
        return {
            "intent": "distinct_videos_with_new_metric_on_day",
            "metric": metric,
            "creator_id": None,
            "threshold": None,
            "date_from": None,
            "date_to": None,
            "day": day,
        }

    raise ValueError("unsupported question")
