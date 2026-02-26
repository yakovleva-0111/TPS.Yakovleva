import json
import re
from datetime import datetime, timezone
from pathlib import Path

import asyncpg
import httpx


DATA_SOURCE_URL = "https://drive.google.com/file/d/1mtBVQtEMZKwUIpVtyb7Yf0kH17lrTgpS/view?usp=sharing"


def _drive_download_url(url: str) -> str:
    m = re.search(r"/d/([^/]+)/", url)
    if not m:
        return url
    file_id = m.group(1)
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def _to_dt(s: str) -> datetime:
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _to_int(x) -> int:
    return 0 if x is None else int(x)


async def _download_json(dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    url = _drive_download_url(DATA_SOURCE_URL)
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.get(url, follow_redirects=True)
    r.raise_for_status()
    dst.write_bytes(r.content)


async def ensure_data_loaded(conn: asyncpg.Connection, json_path: Path) -> None:
    v_count = await conn.fetchval("SELECT COUNT(*) FROM videos;")
    if v_count and v_count > 0:
        return

    if not json_path.exists():
        await _download_json(json_path)

    raw = json.loads(json_path.read_text(encoding="utf-8"))
    videos = raw["videos"] if isinstance(raw, dict) and "videos" in raw else raw

    video_rows: list[tuple] = []
    snapshot_rows: list[tuple] = []
    now = datetime.now(timezone.utc)

    for v in videos:
        video_rows.append(
            (
                v["id"],
                v["creator_id"],
                _to_dt(v["video_created_at"]),
                _to_int(v["views_count"]),
                _to_int(v["likes_count"]),
                _to_int(v["comments_count"]),
                _to_int(v["reports_count"]),
                now,
                now,
            )
        )
        for s in v.get("snapshots", []):
            snapshot_rows.append(
                (
                    s["id"],
                    v["id"],
                    _to_int(s["views_count"]),
                    _to_int(s["likes_count"]),
                    _to_int(s["comments_count"]),
                    _to_int(s["reports_count"]),
                    _to_int(s["delta_views_count"]),
                    _to_int(s["delta_likes_count"]),
                    _to_int(s["delta_comments_count"]),
                    _to_int(s["delta_reports_count"]),
                    _to_dt(s["created_at"]),
                    now,
                )
            )

    async with conn.transaction():
        await conn.executemany(
            """
            INSERT INTO videos
            (id, creator_id, video_created_at, views_count, likes_count, comments_count, reports_count, created_at, updated_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            """,
            video_rows,
        )
        await conn.executemany(
            """
            INSERT INTO video_snapshots
            (id, video_id, views_count, likes_count, comments_count, reports_count,
             delta_views_count, delta_likes_count, delta_comments_count, delta_reports_count, created_at, updated_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            """,
            snapshot_rows,
        )
