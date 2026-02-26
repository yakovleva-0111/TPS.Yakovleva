from datetime import date

METRIC_COL = {
    "views": "views_count",
    "likes": "likes_count",
    "comments": "comments_count",
    "reports": "reports_count",
}

DELTA_COL = {
    "views": "delta_views_count",
    "likes": "delta_likes_count",
    "comments": "delta_comments_count",
    "reports": "delta_reports_count",
}


def build_sql(parsed: dict) -> tuple[str, list]:
    intent = parsed.get("intent")
    metric = parsed.get("metric")

    if intent == "total_metric_sum":
        col = METRIC_COL[metric]
        return (f"SELECT COALESCE(SUM({col}),0) FROM videos;", [])

    if intent == "total_videos_in_month":
        y, m = parsed["month"].split("-")
        y = int(y)
        m = int(m)
        start = date(y, m, 1)
        if m == 12:
            end = date(y + 1, 1, 1)
        else:
            end = date(y, m + 1, 1)
        return (
            "SELECT COUNT(*) FROM videos WHERE video_created_at >= $1::date AND video_created_at < $2::date;",
            [start.isoformat(), end.isoformat()],
        )

    if intent == "creator_videos_in_range":
        return (
            "SELECT COUNT(*) FROM videos WHERE creator_id=$1 AND video_created_at >= $2::date AND video_created_at < ($3::date + interval '1 day');",
            [parsed["creator_id"], parsed["date_from"], parsed["date_to"]],
        )

    if intent == "videos_over_threshold":
        col = METRIC_COL[metric]
        return (
            f"SELECT COUNT(*) FROM videos WHERE {col} > $1;",
            [parsed["threshold"]],
        )

    if intent == "total_delta_on_day":
        col = DELTA_COL[metric]
        return (
            f"SELECT COALESCE(SUM({col}),0) FROM video_snapshots WHERE created_at >= $1::date AND created_at < ($1::date + interval '1 day');",
            [parsed["day"]],
        )

    if intent == "distinct_videos_with_new_metric_on_day":
        col = DELTA_COL[metric]
        return (
            f"SELECT COUNT(DISTINCT video_id) FROM video_snapshots WHERE created_at >= $1::date AND created_at < ($1::date + interval '1 day') AND {col} > 0;",
            [parsed["day"]],
        )

    raise ValueError(f"Unknown intent: {intent}")