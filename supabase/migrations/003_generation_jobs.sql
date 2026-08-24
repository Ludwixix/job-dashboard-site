-- Supabase schema migration: async generation job queue
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard → SQL Editor
--
-- This replaces the synchronous Generate flow. POST /functions/v1/generate no
-- longer blocks ~2min on the OpenRouter LLM call; instead it inserts a queued
-- row here and returns { job_id } instantly. A worker edge function
-- (generate_worker) is woken on an interval (pg_cron + pg_net, or a free
-- GitHub Actions cron fallback — see supabase/pg_cron/README.md) and drains the
-- queue one row at a time: reads resume.md + job_profile.json from Storage,
-- calls OpenRouter, persists into jobs + application_documents, then flips this
-- row to 'completed' (or 'error'). The frontend polls /functions/v1/status?job_id=
-- until it sees 'completed'.

-- 5. Generation jobs (async queue for tailored resume/cover-letter generation)
CREATE TABLE IF NOT EXISTS generation_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  -- Raw payload as POSTed to /generate: { title, company, description, why, location }
  job_data JSONB,
  -- queued -> running -> completed | error
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued', 'running', 'completed', 'error')),
  -- Attempt counter: lets a future recovery step retry stuck 'running' rows
  -- (e.g. a worker that died mid-generation) without losing the payload.
  attempt INT DEFAULT 0,
  -- Human-readable failure detail when status = 'error'.
  error TEXT,
  -- FK to the resolved jobs row the generated docs were persisted against.
  -- Set on 'completed' so the frontend can jump straight to the saved doc.
  application_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  -- Set when the worker finishes (completed or error).
  completed_at TIMESTAMPTZ
);

-- Indexes for the worker's "oldest queued" fetch and for time-based cleanup.
CREATE INDEX IF NOT EXISTS idx_generation_jobs_status ON generation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_generation_jobs_created_at ON generation_jobs(created_at);

-- Auto-update updated_at (same helper shape as jobs; 001 already defines it,
-- so just attach a trigger rather than re-declaring the function).
DROP TRIGGER IF EXISTS generation_jobs_updated_at ON generation_jobs;
CREATE TRIGGER generation_jobs_updated_at
  BEFORE UPDATE ON generation_jobs
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Row Level Security (RLS)
-- Same model as the other tables in 001: service role bypasses RLS (edge
-- functions insert/write through the service key), while authenticated users
-- can read so the frontend /status endpoint stays queryable per the
-- authenticated-read pattern already in the project.
ALTER TABLE generation_jobs ENABLE ROW LEVEL SECURITY;

-- Authenticated users: read-only access (polling /status from a signed-in client)
-- Drop-then-create keeps this idempotent for the GitHub integration re-runs.
DROP POLICY IF EXISTS "Authenticated read generation jobs" ON generation_jobs;
CREATE POLICY "Authenticated read generation jobs"
  ON generation_jobs FOR SELECT
  USING (auth.role() = 'authenticated');

-- Service role (worker edge function) bypasses RLS automatically.
-- No explicit INSERT/UPDATE/DELETE policy needed — denied by default.