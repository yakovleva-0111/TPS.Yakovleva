CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS videos (
  id              UUID PRIMARY KEY,
  creator_id      UUID NOT NULL,
  video_created_at TIMESTAMPTZ NOT NULL,

  views_count     BIGINT NOT NULL,
  likes_count     BIGINT NOT NULL,
  comments_count  BIGINT NOT NULL,
  reports_count   BIGINT NOT NULL,

  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS video_snapshots (
  id                   UUID PRIMARY KEY,
  video_id             UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,

  views_count          BIGINT NOT NULL,
  likes_count          BIGINT NOT NULL,
  comments_count       BIGINT NOT NULL,
  reports_count        BIGINT NOT NULL,

  delta_views_count    BIGINT NOT NULL,
  delta_likes_count    BIGINT NOT NULL,
  delta_comments_count BIGINT NOT NULL,
  delta_reports_count  BIGINT NOT NULL,

  created_at           TIMESTAMPTZ NOT NULL,
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_videos_creator_id ON videos(creator_id);
CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(video_created_at);

CREATE INDEX IF NOT EXISTS idx_snapshots_video_created ON video_snapshots(video_id, created_at);
CREATE INDEX IF NOT EXISTS idx_snapshots_created_at ON video_snapshots(created_at);