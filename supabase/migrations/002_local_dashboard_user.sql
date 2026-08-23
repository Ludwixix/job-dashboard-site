-- Local dashboard user for generated documents.
-- The dashboard has no auth; generated resumes/cover letters are attributed to
-- this fixed user (see generate/index.ts LOCAL_USER_ID). Using a real row in
-- auth.users keeps the application_documents.user_id FK and the
-- UNIQUE(job_id, user_id, document_type, format) constraint satisfied, so
-- regenerating the same role merges instead of duplicating rows.
INSERT INTO auth.users (id, email, raw_app_meta_data, raw_user_meta_data, email_confirmed_at, created_at, updated_at)
VALUES ('00000000-0000-4000-8000-000000000001', 'dashboard-local@localhost', '{}', '{}', now(), now(), now())
ON CONFLICT (id) DO NOTHING;