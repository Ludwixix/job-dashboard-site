-- pg_cron + pg_net registration for the async generation worker.
--
-- IMPORTANT (manual gate 1): In the Supabase dashboard, enable these two
-- extensions BEFORE running this file, or remove the `create extension` lines
-- if already enabled. Run this file in the SQL Editor (you need superuser/
-- dashboard access — the SQL Editor runs as the `postgres` role, not the anon
-- key):
--   Database → Extensions → enable `pg_cron` and `pg_net`
-- (Or just run `create extension if not exists ...` below; the SQL Editor can
-- create extensions on the free plan.)
--
-- IMPORTANT (manual gate 2): The cron job POSTs to your deployed Supabase edge
-- function HTTPS URL. The function must be deployed (the `gateway` will do
-- that). The cron body calls net.http_post which performs an HTTP request from
-- inside Postgres via the pg_net extension.
--
-- The function is invoked WITHOUT auth (public, like the rest of the dashboard
-- endpoints); it enqueues/processes under its service-role env secrets.

create extension if not exists pg_cron;
create extension if not exists pg_net;

-- pg_cron on Supabase runs at MINUTE granularity (this build's cron worker fires
-- schedule rows on a minute boundary, not per-second). Use a minute-based spec.
-- `* * * * * *` = every minute. (A leading `*/30` in the minute slot means "at
-- :00 and :30 of each hour", NOT "every 30 seconds" — that was the first bug hit
-- when deploying this. Do not use a seconds sub-field.)
select cron.schedule(
  'generate-worker-tick',
  '* * * * * *',
  $$
  select net.http_post(
    'https://piussupjoajcxumtmzpp.supabase.co/functions/v1/generate_worker',
    '{}'::jsonb
  );
  $$
);

-- Note: net.http_post must use POSITIONAL args (url, body, params, headers).
-- The named-arg form (`url:=..., headers:=...`) fails inside the cron command
-- executor with `syntax error at or near ":"`, so the invocation above uses the
-- positional form. The default headers already send Content-Type: application/json.

-- To unschedule later:
--   select cron.unschedule('generate-worker-tick');
-- To verify it's registered and inspect run stats:
--   select * from cron.job;
--   select * from cron.job_run_details order by start_time desc limit 20;