import re
from datetime import date


_MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


def parse_ru_day(text: str) -> str:
    t = text.lower()
    m = re.search(
        r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})",
        t,
    )
    if not m:
        raise ValueError("day not found")
    d = int(m.group(1))
    mon = _MONTHS[m.group(2)]
    y = int(m.group(3))
    return date(y, mon, d).isoformat()


def parse_ru_range(text: str) -> tuple[str, str]:
    t = text.lower()

    m = re.search(
        r"с\s+(\d{1,2})\s+по\s+(\d{1,2})\s+"
        r"(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})",
        t,
    )
    if m:
        d1 = int(m.group(1))
        d2 = int(m.group(2))
        mon = _MONTHS[m.group(3)]
        y = int(m.group(4))
        return date(y, mon, d1).isoformat(), date(y, mon, d2).isoformat()

    m = re.search(
        r"с\s+(\d{1,2})\s+"
        r"(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})\s+"
        r"по\s+(\d{1,2})\s+\2\s+\3",
        t,
    )
    if m:
        d1 = int(m.group(1))
        mon = _MONTHS[m.group(2)]
        y = int(m.group(3))
        d2 = int(m.group(4))
        return date(y, mon, d1).isoformat(), date(y, mon, d2).isoformat()

    raise ValueError("range not found")
