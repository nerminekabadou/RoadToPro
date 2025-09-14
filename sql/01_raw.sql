CREATE TABLE IF NOT EXISTS raw_events (
  id BIGSERIAL PRIMARY KEY,
  type TEXT NOT NULL,
  at TIMESTAMPTZ NOT NULL,
  key TEXT NOT NULL,
  source TEXT NOT NULL,
  version TEXT NOT NULL,
  payload JSONB NOT NULL,
  payload_hash BYTEA NOT NULL,
  received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (type, key, payload_hash)
);
