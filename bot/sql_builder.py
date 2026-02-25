from bot.nlu import Query

METRIC_TO_FINAL = {
    "views": "views_count",
    "likes": "likes_count",
    "comments": "comments_count",
    "reports": "reports_count",
}

METRIC_TO_DELTA = {
    "views": "delta_views_count",
    "likes": "delta_likes_count",
    "comments": "delta_comments_count",
    "reports": "delta_reports_count",
}


def build(q: Query) -> tuple[str, tuple]:
    if q.kind == "count_all_videos":
        return "SELECT COUNT(*) FROM videos;", ()
    
    if q.kind == "sum_final_all":
        col = METRIC_TO_FINAL[q.metric or "views"]
        return (f"SELECT COALESCE(SUM({col}), 0) FROM videos;", ())

    if q.kind == "count_videos_by_creator_between":
        return (
            "SELECT COUNT(*) FROM videos WHERE creator_id=$1 AND video_created_at >= $2 AND video_created_at < $3;",
            (q.creator_id, q.start, q.end),
        )
    
    if q.kind == "count_videos_between":
        return (
            "SELECT COUNT(*) FROM videos WHERE video_created_at >= $1 AND video_created_at < $2;",
            (q.start, q.end),
        )

    if q.kind == "count_videos_gt_final":
        col = METRIC_TO_FINAL[q.metric or "views"]
        return (f"SELECT COUNT(*) FROM videos WHERE {col} > $1;", (q.threshold,))

    if q.kind == "sum_delta_by_day":
        col = METRIC_TO_DELTA[q.metric or "views"]
        return (
            f"SELECT COALESCE(SUM({col}), 0) FROM video_snapshots WHERE created_at >= $1 AND created_at < $2;",
            (q.start, q.end),
        )

    if q.kind == "count_distinct_with_positive_delta_by_day":
        col = METRIC_TO_DELTA[q.metric or "views"]
        return (
            f"""
            SELECT COUNT(DISTINCT video_id)
            FROM video_snapshots
            WHERE created_at >= $1 AND created_at < $2 AND {col} > 0;
            """,
            (q.start, q.end),
        )

    raise ValueError(f"Unknown query kind: {q.kind}")