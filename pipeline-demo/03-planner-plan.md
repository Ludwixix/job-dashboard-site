# 🧠 Planner — Implementation Plan for Candidate A

## Goal
Ship a relevance re-scorer that ranks Melbourne IT roles against Sam's real profile and emits a clean shortlist — without touching live dashboard behavior.

## Acceptance criteria
1. Every input job gets a `score` 0-100 (weighted: title 3x, description 2x, tags/why 1x).
2. Output shortlist top N (default 20) with per-role "match reasons" (which skills hit).
3. Reclassification fixes the noisy buckets: exclude electrical/mech/civil etc.
4. Idempotent, pure stdlib, no network. Runnable via `python3 pipeline-demo/score_jobs.py`.
5. Outputs JSON lines + markdown summary (readable, diffable).

## Deliverables
1. `pipeline-demo/score_jobs.py` (Coder)
2. `pipeline-demo/03-shortlist.json` + `03-shortlist.md` (Coder output)
3. `pipeline-demo/04-narrative.md` (Writer synthesis)
4. Review artifacts (Critic/Reviewer) → kickback loop

## Team
| Phase | Agent | Expected |
|-------|-------|----------|
| 1 | Coder | scoring script + shortlist run |
| 2 | Writer | summary narrative from shortlist + audit |
| 3 | Critic | SHARP taste on usefulness (is shortlist actually insightful?) |
| 4 | Reviewer | correctness gate (scores, bucketing, no leakage) |
| 5 | Loop | revisit Coder if Reviewer flags issues |

## Taste gates
- Raw: scores look sane (relevant titles >> irrelevant)
- Refined: shortlist tells Sam something he didn't know

## Risk
- Description coverage gap → score may underweight genuinely good roles missing text. Mitigate: fall back to title+tags scoring, flag low-signal jobs as "insufficient description" rather than low score.