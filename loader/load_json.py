import json
from pathlib import Path


async def load_json(conn, json_path: Path) -> None:
    json_path = Path(json_path)

    # если уже есть данные — не грузим снова
    existing = await conn.fetchval("SELECT COUNT(*) FROM videos;")
    if existing and int(existing) > 0:
        return

    data = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("videos.json must contain a list")

    video_rows = []
    snapshot_rows = []

    for v in data:
        if not isinstance(v, dict):
            continue

        video_id = v.get("id")
        creator_id = v.get("creator_id")
        video_created_at = v.get("video_created_at")

        views = v.get("views_count", 0)
        likes = v.get("likes_count", 0)
        comments = v.get("comments_count", 0)
        reports = v.get("reports_count", 0)

        video_rows.append(
            (video_id, creator_id, video_created_at, views, likes, comments, reports)
        )

        snaps = v.get("snapshots") or v.get("video_snapshots") or []
        if isinstance(snaps, list):
            for s in snaps:
                if not isinstance(s, dict):
                    continue
                snapshot_rows.append(
                    (
                        s.get("id"),
                        video_id,
                        s.get("views_count", 0),
                        s.get("likes_count", 0),
                        s.get("comments_count", 0),
                        s.get("reports_count", 0),
                        s.get("delta_views_count", 0),
                        s.get("delta_likes_count", 0),
                        s.get("delta_comments_count", 0),
                        s.get("delta_reports_count", 0),
                        s.get("created_at"),
                    )
                )

    await conn.executemany(
        """
        INSERT INTO videos (
            id, creator_id, video_created_at,
            views_count, likes_count, comments_count, reports_count
        )
        VALUES ($1,$2,$3,$4,$5,$6,$7)
        ON CONFLICT (id) DO NOTHING;
        """,
        video_rows,
    )

    if snapshot_rows:
        await conn.executemany(
            """
            INSERT INTO video_snapshots (
                id, video_id,
                views_count, likes_count, comments_count, reports_count,
                delta_views_count, delta_likes_count, delta_comments_count, delta_reports_count,
                created_at
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
            ON CONFLICT (id) DO NOTHING;
            """,
            snapshot_rows,
        )