# Async generation worker: trigger setup

`POST /functions/v1/generate` no longer blocks on the OpenRouter LLM call. It
returns `{ job_id, status: 'queued' }` instantly; a **worker edge function**
(`generate_worker`) actually runs the slow LLM call and must be **woken on an
interval**. Supabase doesn't run arbitrary timers on its own, so you pick one of
two free triggers below.

## Primary path (recommended): pg_cron + pg_net (in-database)

This keeps everything inside Supabase — no external service. `pg_cron` fires on
a cron expression, and `pg_net` lets Postgres POST to your edge function URL.

### One-time manual steps (operator)

1. **Enable the two extensions** in the Supabase dashboard:
   Database → **Extensions** → search and enable **`pg_cron`** and **`pg_net`**.
   (Or just run the `create extension` lines in `setup.sql` from the SQL Editor —
   the dashboard SQL Editor runs as the superuser and can create them.)
2. **Deploy the `generate_worker` function** (the gateway does this, but it must
   exist before the cron can call it). It is invoked as a public POST; it runs
   under its own service-role env secrets.
3. **Register the cron job** by running the whole file
   `supabase/pg_cron/setup.sql` in the SQL Editor.

Prerequisite for this path: your project plan must support `pg_net`. It is
available on all Supabase plans (including free), but it may need enabling once
as above. If `create extension if not exists pg_net;` errors, use the GitHub
Actions fallback instead.

The cron schedule is the 6-field `*/30 * * * * *` (every 30 seconds). To change interval, edit the
cron expression in `setup.sql` and re-run `cron.unschedule` + `cron.schedule`.

Register   : run `supabase/pg_cron/setup.sql` in the SQL Editor.
Verify     : `select * from cron.job;`
Inspect run: `select * from cron.job_run_details order by start_time desc limit 20;`
Remove     : `select cron.unschedule('generate-worker-tick');`

## Fallback path: GitHub Actions cron (free)

If `pg_net` cannot be enabled on your plan, a free GitHub Actions workflow POSTs
to the worker every few minutes instead. No dashboard clicks beyond enabling the
workflow.

Activate: `.github/workflows/worker-cron.yml` is already staged. Enable it via
GitHub → repo → **Actions** → the **worker-cron** workflow → **Enable**. Edit the
`schedule` cron in that file to change cadence (default every 5 min).

> Free-plan GitHub Actions runs may be delayed several minutes behind schedule —
> acceptable for a `~2 min` generation. The pg_cron path is the tight (30s) one.

## Which one should you use?

| Path | Latency | Setup | Runtime cost |
|------|---------|-------|--------------|
| pg_cron + pg_net | ~30s polls | 2 extension enables + 1 SQL file | $0 (in-db) |
| GitHub Actions  | ~5 min polls | enable 1 workflow | $0 (free tier) |

**Primary: pg_cron + pg_net.** Only switch to GitHub Actions if the `pg_net`
extension can't be enabled on your plan. You can also run both; the worker is
re-entrant and will simply process the queue sooner.