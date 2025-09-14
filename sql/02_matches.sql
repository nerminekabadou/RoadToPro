-- 02_matches.sql (generic across games, works for LoL/VAL/CS2 later)
CREATE TABLE IF NOT EXISTS matches (
  game              TEXT NOT NULL,           -- e.g., 'lol'
  match_id          BIGINT PRIMARY KEY,
  slug              TEXT,
  name              TEXT,
  status            TEXT,                    -- not_started|running|finished|canceled|postponed
  live              BOOLEAN,
  best_of           INT,
  league_id         BIGINT,
  league_slug       TEXT,
  league            TEXT,
  tournament_id     BIGINT,
  tournament_slug   TEXT,
  tournament        TEXT,
  serie_id          BIGINT,
  opponent1_id      BIGINT,
  opponent1_slug    TEXT,
  opponent1         TEXT,
  opponent2_id      BIGINT,
  opponent2_slug    TEXT,
  opponent2         TEXT,
  scheduled_at      TIMESTAMPTZ,
  begin_at          TIMESTAMPTZ,
  end_at            TIMESTAMPTZ,
  start_time        TIMESTAMPTZ GENERATED ALWAYS AS (COALESCE(begin_at, scheduled_at)) STORED,
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_matches_start_status ON matches (start_time, status);
CREATE INDEX IF NOT EXISTS idx_matches_tournament ON matches (tournament_id);
CREATE INDEX IF NOT EXISTS idx_matches_league ON matches (league_id);

