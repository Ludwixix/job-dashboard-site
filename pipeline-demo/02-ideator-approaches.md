# 💡 Ideator — Candidate Approaches (artifact)

Prepared for: job-dashboard `jobs_nonlinkedin_2026-08-23_final.json`
Goal: make the dashboard actually useful for Sam (prioritize genuinely relevant Melbourne IT roles).

## Context from survey
- 780 jobs, but **all score=0** → current ranking is dead.
- Classifier noisy: mixes electrical/etc. into IT buckets; 170 unclassified.
- Description coverage only 67%; salary only 8%.

## 3 candidate angles (ACE-scored)

### Candidate A — Keyword + role-relevance re-scorer (recommended)
Re-score all 780 jobs against Sam's documented profile (resume.md source of truth: Entra ID, Intune, M365, ServiceNow, SharePoint, PowerShell, endpoint mgmt, ITIL, L2/3). Weighted title>description>why. Re-classify reliably.
- **A**: 5 — directly solves "what do I actually apply to?"
- **C**: 3 — modest; a scorer is standard, value is in mapping to Sam's real stack
- **E**: 5 — trivial, pure JSON + keyword rules, no external deps
- **Overall**: 🟢 Strongly recommend

**B — Salary + seniority enrichment**
Add salary range parsing and seniority band (L1/L2/L3/Lead) from title/keywords so Sam can filter on both.
- **A**: 3 — nice but secondary
- **C**: 2 — tiny contribution
- **E**: 3 — needs salary data quality (only 11% present)
- **Overall**: 🟡 Promising, lower ceiling

### C — "Zero-overlap" gap detector
Report the gap between required skills in top matches vs Sam's profile, so he knows which to brush up on.
- **A**: 4 — genuinely useful for targeting
- **C**: 2 — simple keyword diff
- **E**: 4 — moderate
- **Overall**: 🟡 Promising; depends on A first (needs clean relevance scoring to be meaningful)

## Recommendation
Pursue **A** now. Add **C** on top once A's scores are trustworthy. B is optional polish.

## Contribution statement (draft for later doc)
- Re-scorer classifies Melbourne IT listings against Sam's documented stack
- Produces a ranked shortlist + per-role match reasons
- Fixes the broken 0-score signal end-to-end

## Target consumer
Sam, daily job triage. Also re-points existing dashboard generator (non-destructive: output to pipeline-demo/).