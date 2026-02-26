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

    if intent == "total_videos":
        return "SELECT COUNT(*) FROM videos;", []

    if intent == "creator_videos_in_range":
        return (
            "SELECT COUNT(*) FROM videos "
            "WHERE creator_id=$1 "
            "AND video_created_at >= $2::date "
            "AND video_created_at < ($3::date + interval '1 day');",
            [parsed.get("creator_id"), parsed.get("date_from"), parsed.get("date_to")],
        )

    if intent == "videos_over_threshold":
        col = METRIC_COL[metric]
        return (f"SELECT COUNT(*) FROM videos WHERE {col} > $1;", [int(parsed.get("threshold") or 0)])

    if intent == "total_delta_on_day":
        col = DELTA_COL[metric]
        return (
            f"SELECT COALESCE(SUM({col}),0) FROM video_snapshots "
            "WHERE created_at >= $1::date AND created_at < ($1::date + interval '1 day');",
            [parsed.get("day")],
        )

    if intent == "distinct_videos_with_new_metric_on_day":
        col = DELTA_COL[metric]
        return (
            f"SELECT COUNT(DISTINCT video_id) FROM video_snapshots "
            "WHERE created_at >= $1::date AND created_at < ($1::date + interval '1 day') "
            f"AND {col} > 0;",
            [parsed.get("day")],
        )

    raise ValueError("unknown intent")
