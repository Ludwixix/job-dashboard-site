# ✍️ Writer — Narrative Summary (artifact)

## What the audit found
The job dashboard is collecting real listings — 780 live Melbourne roles across Adzuna (522), Seek (243), Indeed (15) — but it cannot currently rank them. Every record carries `score: 0`, so the interface offers no answer to Sam's core question: *"which of these should I actually spend my day on?"* Two further data-quality issues compound this: the classifier is noisy (an electrical "Senior Power Systems Engineer" sits in `infrastructure-systems` while genuinely strong matches like "Technology Support Analyst" sit unclassified), and only 67% of listings carry enough description to fully score at signal.

## What we did about it
Built a pure-stdlib re-scorer that weights each listing's title 3x, description 2x, and tags/why 1x against Sam's documented stack — M365, Entra ID, Intune/Autopilot, ServiceDesk, SharePoint, ServiceNow, ITIL, PowerShell, endpoint management. It now emits a ranked shortlist with explicit per-role match reasons, and applies discipline exclusions so off-domain engineering roles cannot crowd the top of the list.

## The shortlist, in plain terms
The top of the file is exactly where it should be:
1. **Lead Engineer — Azure Cloud & DevOps (LAB3)** — direct Azure/DevOps/automation fit
2. **Senior Cloud Automation Consultant (XPT)** — infra/config/deployment + automation
3. **M365 Consultant, SharePoint & Power Platform (Arinco)** — pure M365/SharePoint
4. **Identity Engineer, Okta/Entra ID (Milestone IT)** — identity + IAM
5. **IT Engineer — Cloud & Entra ID (Yarra Trams)** — Melbourne CBD, Entra + infra

Notable: Microsoft Corp's "Azure Cloud & AI **Sales** Specialist" ranks mid-table (score ~51) — it matches on keywords but is a quota-role, a classic case where a rescorer over-weights title keywords over role function. That is a refinement for the loop.

## Honest caveat
This first pass proves the mechanism; it is not yet a tuned product. The score is keyword-weighted, not semantic, so a human check of the top 20 (or a follow-up using gbrain on descriptions) is the right next step before calling the shortlist "the" answer.

---

*Written by: Writer agent. Inputs: survey audit (02), plan (03), coder script + shortlist (03-*).*