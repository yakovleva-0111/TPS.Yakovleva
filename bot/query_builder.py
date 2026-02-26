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


def _d(s: str) -> date:
    return date.fromisoformat(s)


def build_sql(parsed: dict) -> tuple[str, list]:
    intent = parsed.get("intent")
    metric = parsed.get("metric")

    if intent == "total_metric_sum":
        col = METRIC_COL[metric]
        return (f"SELECT COALESCE(SUM({col}),0) FROM videos;", [])

    if intent == "total_videos_in_month":
        if not parsed.get("month"):
            raise ValueError("month is required for total_videos_in_month")

        y, m = parsed["month"].split("-")
        y = int(y)
        m = int(m)
        start = date(y, m, 1)
        end = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
        return (
            "SELECT COUNT(*) FROM videos WHERE video_created_at >= $1 AND video_created_at < $2;",
            [start, end],
        )

    if intent == "creator_videos_in_range":
        return (
            "SELECT COUNT(*) FROM videos "
            "WHERE creator_id=$1 AND video_created_at >= $2 AND video_created_at < ($3 + interval '1 day');",
            [parsed["creator_id"], _d(parsed["date_from"]), _d(parsed["date_to"])],
        )

    if intent == "videos_over_threshold":
        col = METRIC_COL[metric]
        return (f"SELECT COUNT(*) FROM videos WHERE {col} > $1;", [int(parsed["threshold"])])

    if intent == "total_delta_on_day":
        col = DELTA_COL[metric]
        return (
            f"SELECT COALESCE(SUM({col}),0) FROM video_snapshots "
            "WHERE created_at >= $1 AND created_at < ($1 + interval '1 day');",
            [_d(parsed["day"])],
        )

    if intent == "distinct_videos_with_new_metric_on_day":
        col = DELTA_COL[metric]
        return (
            f"SELECT COUNT(DISTINCT video_id) FROM video_snapshots "
            "WHERE created_at >= $1 AND created_at < ($1 + interval '1 day') AND {col} > 0;",
            [_d(parsed["day"])],
        )

    raise ValueError(f"Unknown intent: {intent}")