import re

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


def _pick_metric(text: str) -> str | None:
    t = text.lower()
    for k, v in _METRIC.items():
        if k in t:
            return v
    return None


def fallback_parse(question: str) -> dict:
    q = (question or "").strip()
    t = q.lower()

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
