import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}

@dataclass
class Query:
    kind: str
    creator_id: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    threshold: int | None = None
    metric: str | None = None  # views/likes/comments/reports


def _parse_ru_date(text: str) -> datetime:
    m = re.search(r"(\d{1,2})\s+([а-яё]+)\s+(\d{4})", text.lower())
    if not m:
        raise ValueError("date not found")
    day = int(m.group(1))
    month = MONTHS[m.group(2)]
    year = int(m.group(3))
    return datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)


def _day_range(day: datetime) -> tuple[datetime, datetime]:
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


def parse(text: str) -> Query:
    t = (text or "").strip().lower()

    metric = None
    if "просмотр" in t:
        metric = "views"
    elif "лайк" in t:
        metric = "likes"
    elif "коммент" in t:
        metric = "comments"
    elif "жалоб" in t or "репорт" in t:
        metric = "reports"

    #"Какое общее количество лайков/просмотров/комментариев/жалоб набрали все видео?"
    if metric is not None and (
        "общее количество" in t
        or ("в сумме" in t and ("набрал" in t or "набрали" in t))
        or ("суммарн" in t)
    ):
        return Query(kind="sum_final_all", metric=metric)

    #"Сколько всего видео есть в системе?"
    if re.search(r"сколько\s+всего\s+видео", t):
        return Query(kind="count_all_videos")
    
    #"Сколько видео появилось на платформе за май 2025"
    m = re.search(r"за\s+([а-яё]+)\s+(\d{4})", t)
    if "сколько" in t and "видео" in t and m:
        month_name = m.group(1)
        year = int(m.group(2))
        if month_name in MONTHS:
            month = MONTHS[month_name]
            start = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
            if month == 12:
                end = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            else:
                end = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            return Query(kind="count_videos_between", start=start, end=end)
        

    #"Сколько видео у креатора с id ... вышло с ... по ... включительно?"
    m = re.search(r"креатор[а-я]*\s+с\s+id\s+([0-9a-f\-]{8,})", t)
    creator_id = m.group(1) if m else None
    if "вышл" in t and "по" in t and "с" in t and creator_id is not None:
        m1 = re.search(r"с\s+(\d{1,2}\s+[а-яё]+\s+\d{4})", t)
        m2 = re.search(r"по\s+(\d{1,2}\s+[а-яё]+\s+\d{4})", t)
        if m1 and m2:
            d1 = _parse_ru_date(m1.group(1))
            d2 = _parse_ru_date(m2.group(1))
            start = d1
            end = _day_range(d2)[1] 
            return Query(kind="count_videos_by_creator_between", creator_id=creator_id, start=start, end=end)

    #"Сколько видео набрало больше 100 000 просмотров за всё время?"
    if "набрал" in t and "больше" in t and "за всё время" in t:
        num = re.search(r"больше\s+([\d\s]+)", t)
        if num:
            threshold = int(num.group(1).replace(" ", ""))
            return Query(kind="count_videos_gt_final", threshold=threshold, metric=metric or "views")

    #"На сколько просмотров в сумме выросли все видео 28 ноября 2025?"
    if "на сколько" in t and "в сумме" in t and ("выросл" in t or "приросл" in t):
        day = _parse_ru_date(t)
        start, end = _day_range(day)
        return Query(kind="sum_delta_by_day", start=start, end=end, metric=metric or "views")

    #"Сколько разных видео получали новые просмотры 27 ноября 2025?"
    if "сколько разных видео" in t and ("получал" in t or "получили" in t) and ("новые" in t or "нов" in t):
        day = _parse_ru_date(t)
        start, end = _day_range(day)
        return Query(kind="count_distinct_with_positive_delta_by_day", start=start, end=end, metric=metric or "views")

    raise ValueError("Не смогла распознать запрос")