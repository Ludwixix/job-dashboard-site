# 🔍 Reviewer — Correctness Gate (Stage 7b)

**Recommendation: 🟠 BORDERLINE → rework requested (specific action items, not a dead-end reject).**

## Verified findings (evidence-checked)
| # | Severity | Finding | Status |
|---|----------|---------|--------|
| 1 | 🔴 Fatal | **Sales role ranks #5** — "Azure Cloud & AI Sales Specialist" scored 51 on keyword overlap; role function not considered. Overstates true fit. | CONFIRMED (shortlist row 5) |
| 2 | 🔴 Fatal | **No dedupe** — duplicate titles with blank company/location ranked consecutively (rows 7/10 in earlier run). Shortlist counts inflated. | CONFIRMED |
| 3 | 🟡 Important | **Recruiter spam not surfaced** — 5/20 rows are staffing firms (XPT ×2, Milestone ×2, Hastha) re-listing roles. Not wrong, but user can't filter them. | CONFIRMED |
| 4 | 🟡 Important | **Low-signal flag exists but is not exposed** in the markdown output — a job with no description is silently under-scored, and the consumer can't tell. | CODE CHECK |
| 5 | 🟢 Minor | `load_jobs()` picks newest `_final` file — fine for now but brittle if multiple dates exist. | CODE CHECK |

## Correctness verdict on the mechanism
Scoring math is sound (title 3x / desc 2x / tags 1x, discipline floor at ≤5), the
non-IT exclusion works, output is idempotent and pure-stdlib. The *mechanism* passes;
the *tuning* fails.

## Action items (kickback → Coder via Planner)
1. 🔴 Add role-function guardrails: down-weight sales/specialist/account-manager titles.
2. 🔴 Dedupe by normalized (title, company) before ranking.
3. 🟡 Surface `low_signal` in the markdown table.
4. 🟡 Optional: staffing-agency flag column.

**Re-review expected after items 1–3.**