SCHEMA = """База PostgreSQL содержит две таблицы.

videos
- id (uuid) — id видео
- creator_id (uuid) — id креатора
- video_created_at (timestamptz) — время публикации
- views_count, likes_count, comments_count, reports_count (bigint) — итоговые значения

video_snapshots
- id (uuid) — id снапшота
- video_id (uuid) — ссылка на videos.id
- views_count, likes_count, comments_count, reports_count (bigint) — значения на момент замера
- delta_views_count, delta_likes_count, delta_comments_count, delta_reports_count (bigint) — приращения относительно прошлого замера
- created_at (timestamptz) — время замера (раз в час)
"""


def build_system_prompt_for_nlu() -> str:
    return f"""Ты распознаёшь пользовательский запрос на русском и возвращаешь JSON с параметрами.

СХЕМА ДАННЫХ:
{SCHEMA}

ДОПУСТИМЫЕ intent:
- total_videos
- creator_videos_in_range
- videos_over_threshold
- total_delta_on_day
- distinct_videos_with_new_metric_on_day

ДОПУСТИМЫЕ metric:
views | likes | comments | reports

ФОРМАТ ОТВЕТА (строго JSON, без текста):
{{
  "intent": "...",
  "metric": "views|likes|comments|reports|null",
  "creator_id": "uuid|null",
  "threshold": 0|null,
  "date_from": "YYYY-MM-DD|null",
  "date_to": "YYYY-MM-DD|null",
  "day": "YYYY-MM-DD|null"
}}

ПРАВИЛА:
- "с 1 ноября 2025 по 5 ноября 2025 включительно" => date_from=2025-11-01, date_to=2025-11-05
- "с 1 по 5 ноября 2025" => date_from=2025-11-01, date_to=2025-11-05
- "28 ноября 2025" => day=2025-11-28
- "новые просмотры" => distinct_videos_with_new_metric_on_day (delta > 0)
- "на сколько ... выросли" => total_delta_on_day (SUM(delta_*))

Верни только JSON.
""".strip()
