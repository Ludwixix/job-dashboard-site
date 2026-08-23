# 🎯 Critic — Taste Gate (Stage 7a)

**Verdict: 🟡 RAW → needs refinement before use. Do not ship as-is.**

## What's genuinely good
- The core question is the right one ("which of these 780 do I spend my day on?"), and the
  mechanism answers it. LAB3 Azure/DevOps at #1, Arinco M365 at #3 — the shape of a good
  answer is visible.
- Per-role match reasons are honest; nothing is hidden behind a black-box score.

## Why it fails the taste bar
1. **A sales role at #5 overall.** `Azure Cloud & AI Sales Specialist — Microsoft` scoring
   51 on "microsoft, it support, azure, cloud" is exactly the "keyword match ≠ role fit"
   failure I exist to catch. The one-sentence insight test fails: *"the shortlist separates
   real engineering roles from everything else"* — it does not, until this is fixed.
2. **No negative signal for recruiter-spam.** 5 of 20 rows are staffing-mills (XPT, Milestone,
   Hastha) re-listing the same role. The shortlist should surface companies, not duplicate
   aggregator noise.
3. **Duplicates with blank company/location ranked next to each other (rows 7/10).** That's
   the kind of artifact a discerning reader notices in seconds.

## Improvement direction (handed to Coder via Planner)
- Add role-function guardrails: `sales`, `specialist`, `account manager` must down-weight
  titles even with azure/microsoft words.
- Dedupe by title+company before scoring; weight aggregator/staffing firms down.
- Then re-run. I'll re-gate.

*Taste bar: the shortlist must tell Sam something he didn't already know. Right now it tells
him "Azure jobs are relevant" — that's table stakes.*