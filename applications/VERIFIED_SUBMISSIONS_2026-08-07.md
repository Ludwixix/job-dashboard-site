# Verified LinkedIn Submissions — August 7, 2026

This ledger records only submissions with evidence from the current controlled campaign. Legacy ApplyPilot and ClawApply records are not treated as proof of current submission unless independently verified.

## Confirmed submissions

| Role | Employer | LinkedIn job ID | Evidence | Submission time |
|---|---|---:|---|---|
| Senior System Engineer – L.3 | Salt | `4448922694` | Approved runner recorded LinkedIn confirmation and tracker lifecycle `submitted` | August 7, 2026, 10:27:35 a.m. |
| IT Systems Engineer — 12-month FTC | 12m FTC | `4447698586` | Approved runner detected LinkedIn confirmation text and recorded `submitted` | August 7, 2026, 11:46:41 a.m. |
| Onsite Support Engineer | Coforge | `4445464366` | Approved runner detected LinkedIn confirmation text and recorded `submitted` after the resumable form was completed with verified profile data | August 7, 2026, 2:11:23 p.m. |

## Campaign controls

- Submission required both `allow_submit: true` and the explicit `--approve-submit` switch.
- External applications were disabled.
- Unsupported screening questions were left unanswered and routed to review.
- No AKS experience was claimed.
- No LinkedIn outreach was sent.

## Audit notes

- `claw-apply/logs/urgent_melbourne_batch.json` is a last-run result file, not an append-only ledger. Its current contents document the 12-month FTC submission only.
- The ClawApply database contains historical and current lifecycle records together. Aggregate counts must not be interpreted as the number of verified submissions from this campaign without filtering by campaign evidence.
- Several newly searched roles were skipped because LinkedIn redirected their apparent Easy Apply controls to search results rather than opening an application form.
- The Coforge form was resumable and succeeded after the verified immediate-availability handling was applied. No unsupported screening answer was used.
- No application runner was active when this ledger was updated.
