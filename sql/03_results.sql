
-- 03_results.sql
CREATE TABLE IF NOT EXISTS results (
  match_id   BIGINT PRIMARY KEY REFERENCES matches(match_id) ON DELETE CASCADE,
  winner_id  BIGINT,
  forfeit    BOOLEAN,
  draw       BOOLEAN,
  end_at     TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);