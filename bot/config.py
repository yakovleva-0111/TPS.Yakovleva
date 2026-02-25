import os


def get_env(name: str, default: str | None = None) -> str:
    val = os.getenv(name, default)
    if val is None or val == "":
        raise RuntimeError(f"Missing env var: {name}")
    return val


BOT_TOKEN = get_env("BOT_TOKEN")

DB_HOST = get_env("DB_HOST", "db")
DB_PORT = int(get_env("DB_PORT", "5432"))
DB_NAME = get_env("DB_NAME", "tps")
DB_USER = get_env("DB_USER", "postgres")
DB_PASSWORD = get_env("DB_PASSWORD", "postgres")

DB_DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"