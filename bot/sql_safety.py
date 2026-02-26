import re

_FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke)\b", re.I)

def assert_safe_select(sql: str) -> str:
    s = (sql or "").strip().rstrip(";")
    if not s.lower().startswith("select"):
        raise ValueError("only SELECT allowed")
    if _FORBIDDEN.search(s):
        raise ValueError("forbidden keyword")
    return s
