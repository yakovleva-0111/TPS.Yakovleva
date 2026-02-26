import os

def _env(name: str, default: str | None = None) -> str:
    val = os.getenv(name, default)
    return "" if val is None else val

BOT_TOKEN = _env("BOT_TOKEN")

DB_HOST = _env("DB_HOST", "db")
DB_PORT = int(_env("DB_PORT", "5432") or 5432)
DB_NAME = _env("DB_NAME", "tps")
DB_USER = _env("DB_USER", "postgres")
DB_PASSWORD = _env("DB_PASSWORD", "postgres")
DB_DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

GIGACHAT_AUTH_KEY = _env("GIGACHAT_AUTH_KEY", "")
GIGACHAT_SCOPE = _env("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
GIGACHAT_MODEL = _env("GIGACHAT_MODEL", "GigaChat")
GIGACHAT_VERIFY_SSL = (_env("GIGACHAT_VERIFY_SSL", "1") or "1") == "1"
