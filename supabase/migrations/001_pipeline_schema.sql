-- Supabase schema migration for job dashboard pipeline
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard → SQL Editor

-- 1. Jobs table (main job listings)
CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source TEXT NOT NULL DEFAULT 'unknown',
  source_record_id TEXT,
  canonical_url TEXT UNIQUE NOT NULL,
  application_route TEXT,
  application_route_type TEXT DEFAULT 'Direct listing',
  listing_verification TEXT DEFAULT 'Verify before applying',
  title TEXT NOT NULL,
  company TEXT NOT NULL,
  location TEXT DEFAULT 'Melbourne',
  description TEXT,
  salary_min NUMERIC,
  salary_max NUMERIC,
  work_type TEXT,
  remote BOOLEAN DEFAULT false,
  posted_at TIMESTAMPTZ,
  is_expired BOOLEAN DEFAULT false,
  screening_score NUMERIC,
  fit TEXT DEFAULT 'Review',
  matched_terms JSONB DEFAULT '[]',
  evidence JSONB DEFAULT '[]',
  gaps JSONB DEFAULT '[]',
  requirements_to_confirm JSONB DEFAULT '[]',
  confidence NUMERIC,
  needs_human_review BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Application documents (generated resume, cover letter, email)
CREATE TABLE IF NOT EXISTS application_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  user_id UUID,
  document_type TEXT NOT NULL CHECK (document_type IN ('resume', 'cover_letter', 'opening_email')),
  format TEXT NOT NULL DEFAULT 'markdown',
  content TEXT NOT NULL,
  source_model TEXT,
  source_prompt_version TEXT,
  is_draft BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(job_id, user_id, document_type, format)
);

-- 3. Interview preparations
CREATE TABLE IF NOT EXISTS interview_preparations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  user_id UUID,
  resume_version TEXT DEFAULT 'current-profile',
  questions JSONB DEFAULT '[]',
  technical_topics JSONB DEFAULT '[]',
  talking_points JSONB DEFAULT '[]',
  evidence_prompts JSONB DEFAULT '[]',
  risks_and_gaps JSONB DEFAULT '[]',
  source_model TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(job_id, user_id)
);

-- 4. Status history (track stage changes)
CREATE TABLE IF NOT EXISTS status_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  old_status TEXT,
  new_status TEXT NOT NULL,
  changed_by UUID,
  changed_at TIMESTAMPTZ DEFAULT now(),
  notes TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_canonical_url ON jobs(canonical_url);
CREATE INDEX IF NOT EXISTS idx_jobs_screening_score ON jobs(screening_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_jobs_is_expired ON jobs(is_expired);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_application_documents_job_id ON application_documents(job_id);
CREATE INDEX IF NOT EXISTS idx_status_history_job_id ON status_history(job_id);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS jobs_updated_at ON jobs;
CREATE TRIGGER jobs_updated_at
  BEFORE UPDATE ON jobs
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Row Level Security (RLS)
-- Updated 2026-08-22: Tightened policies. Service role bypasses RLS by default
-- in Supabase, so no explicit 'service role' policy is needed. Authenticated
-- users can read; only the service role (edge functions, n8n) can write.
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE application_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_preparations ENABLE ROW LEVEL SECURITY;
ALTER TABLE status_history ENABLE ROW LEVEL SECURITY;

-- Authenticated users: read-only access
-- Idempotent: the Supabase GitHub integration re-runs migrations on every
-- push, and CREATE POLICY has no IF NOT EXISTS. Drop-then-create makes
-- this re-runnable against a DB that already has these policies.
DROP POLICY IF EXISTS "Authenticated read jobs" ON jobs;
CREATE POLICY "Authenticated read jobs" ON jobs FOR SELECT USING (auth.role() = 'authenticated');
DROP POLICY IF EXISTS "Authenticated read documents" ON application_documents;
CREATE POLICY "Authenticated read documents" ON application_documents FOR SELECT USING (auth.role() = 'authenticated');
DROP POLICY IF EXISTS "Authenticated read prep" ON interview_preparations;
CREATE POLICY "Authenticated read prep" ON interview_preparations FOR SELECT USING (auth.role() = 'authenticated');
DROP POLICY IF EXISTS "Authenticated read history" ON status_history;
CREATE POLICY "Authenticated read history" ON status_history FOR SELECT USING (auth.role() = 'authenticated');

-- Service role (used by edge functions / n8n) bypasses RLS automatically.
-- No explicit INSERT/UPDATE/DELETE policy needed — denied by default.

-- Insert existing data from the dashboard (if any)
-- This is a one-time migration; existing PDFs in /applications/ are already deployed
