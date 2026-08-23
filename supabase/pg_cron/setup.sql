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

-- pg_cron uses SIX-field cron (second minute hour day month weekday), so
-- the leading */30 means "every 30 seconds" (0 and 30 of the seconds field).
select cron.schedule(
  'generate-worker-tick',
  '*/30 * * * * *',
  $$
  select net.http_post(
    url:='https://piussupjoajcxumtmzpp.supabase.co/functions/v1/generate_worker',
    headers: '{"Content-Type":"application/json"}'::jsonb,
    body: '{}'::jsonb
  );
  $$
);

-- To unschedule later:
--   select cron.unschedule('generate-worker-tick');
-- To verify it's registered and inspect run stats:
--   select * from cron.job;
--   select * from cron.job_run_details order by start_time desc limit 20;