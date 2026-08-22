# Job Dashboard — Architecture & Context

> **Living document.** Maintained by the `job-dashboard` agent. Do not edit manually.
> Last updated: 2026-08-22T12:12:00+10:00

---

## Overview

Sam's personal job-search dashboard. A static site deployed to Netlify at **https://job-dashboard-sam.netlify.app**, password-protected. Aggregates job listings from multiple sources (Seek, Indeed, LinkedIn), scores them against Sam's profile, generates tailored CVs/cover letters, and tracks application stages.

---

## Data Flow Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  SCRAPING                                                       │
│                                                                 │
│  scrape_daily.py ──► jobspy_scraper.py ──► seek_scraper.py     │
│       │                    │                      │             │
│       │                    ▼                      ▼             │
│       │         jobs_nonlinkedin_*.json    (Playwright-based)   │
│       │                                                         │
│  Sources: Seek API v5, Indeed, LinkedIn (tagged for review)     │
│  Location: Melbourne VIC + Remote                               │
│  Categories: 30+ search terms across IT specialisations         │
│  Config: scrape-config.json (search terms, proxy, rate limits)  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  PROCESSING                                                     │
│                                                                 │
│  job_pipeline/it_subcategories.py                               │
│       ├── classify_all() → 7 subcategories                     │
│       └── Keyword rules: title (3x weight) + tags + why field  │
│                                                                 │
│  Scoring: Against Sam's profile (skills, experience, location)  │
│  Audit: Matched terms + unverified/gap analysis                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  DASHBOARD BUILD                                                │
│                                                                 │
│  build_nonlinkedin_dashboard.py (main generator)                │
│       ├── Reads: jobs_nonlinkedin_*.json                        │
│       ├── Classifies into 7 IT subcategories                   │
│       ├── 4 lane view: Core, Local, Outdoor, Technician        │
│       ├── 6-per-section default, dropdown for overflow          │
│       ├── Stage tracking (localStorage persistence)             │
│       └── Outputs: job-dashboard-site/index.html                │
│                                                                 │
│  build_application_pdfs.py (PDF builder)                        │
│       ├── Reads: applications/*.md                              │
│       ├── Outputs: job-dashboard-site/applications/*.pdf        │
│       └── Also generates per-role ZIP packs                     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  DEPLOYMENT                                                     │
│                                                                 │
│  netlify deploy --prod --site 909bff86-...                      │
│  From: job-dashboard-site/ directory                            │
│                                                                 │
│  Post-deploy: HTTP 401 check (password gate), card count match  │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Inventory

### Root (`C:\Users\samlu\.openclaw\workspace\`)

| File | Size | Purpose | Last Modified |
|------|------|---------|---------------|
| `build_nonlinkedin_dashboard.py` | 56KB | **Main dashboard generator.** Reads job JSON, classifies, renders HTML. | 2026-08-22 12:05 |
| `build_application_pdfs.py` | 8.7KB | PDF builder for per-role CVs and cover letters. | 2026-08-19 11:50 |
| `build_aug12_job_packs.py` | 27KB | Batch job pack builder (historical). | 2026-08-12 |
| `build_dashboard_2026_08_22.py` | 28KB | Dashboard variant (date-specific). | 2026-08-22 02:17 |
| `generate_dashboard.py` | 50KB | Alternative dashboard generator (newer). | 2026-08-22 04:00 |
| `scrape_daily.py` | 13KB | Daily scrape orchestrator with rate limiting + proxy support. | 2026-08-22 02:24 |
| `jobspy_scraper.py` | 17.5KB | Enhanced JobSpy scraper wrapper. | 2026-08-22 02:31 |
| `seek_scraper.py` | 12.6KB | Seek.com.au scraper with Playwright Cloudflare bypass. | 2026-08-22 12:10 |
| `scrape-config.json` | 1.8KB | Scraper config (search terms, proxy, rate limits). | 2026-08-22 02:30 |
| `jobs_nonlinkedin_2026-08-08.json` | 851KB | Current job data file (source of truth). | 2026-08-22 12:11 |
| `jobs_dashboard_nonlinkedin_2026-08-08.html` | 2.5MB | Standalone dashboard HTML export. | 2026-08-22 12:11 |
| `job_profile.json` | 7.8KB | Sam's skills, experience, and preferences. | 2026-06-15 |
| `resume.md` | 39KB | Sam's resume (Markdown source). | 2026-06-30 |
| `Sam_Ludwig_Resume_MASTER.pdf` | 7KB | Master resume PDF. | 2026-06-10 |
| `_refresh_2026_08_21_data.py` | 21KB | Data refresh script (2026-08-21). | 2026-08-21 09:27 |
| `application_pack_index.json` | 15KB | Application pack index (role → file mapping). | 2026-08-21 09:27 |

### Pipeline (`job_pipeline/`)

| File | Purpose |
|------|---------|
| `it_subcategories.py` | 7-category IT job classifier with keyword rules |
| `generate_pdf.py` | PDF generation utility |
| `generate_dashboard.py` | Pipeline-level dashboard generator |
| `resume_builder.py` | Resume/cover letter builder |
| `job_matcher.py` | Job scoring against Sam's profile |
| `batch_process.py` | Batch processing utilities |
| `seek_scraper.py` | Seek scraper (pipeline version) |
| `search_processor.py` | Search query processing |
| `pipeline_config.py` | Pipeline configuration |
| `run_pipeline.py` | Pipeline runner script |
| `track_applications.py` | Application tracking |
| `save_mcp_results.py` | MCP result persistence |
| `ap_bridge.py` | Application pipeline bridge |
| `ap_import_bridge.py` | AP import bridge |
| `deepseek_apply*.py` | DeepSeek-powered application automation (v1–v4) |
| `linkedin_apply*.py` | LinkedIn application automation (v1–v2) |
| `linkedin_easy_apply.py` | LinkedIn Easy Apply automation |
| `linkedin_full.py` | Full LinkedIn automation |
| `pipeline_state.json` | Pipeline state persistence |
| `applications_tracker.json` | Application tracker state |
| `applypilot_state.json` | ApplyPilot state |
| `seek_results/` | Seek API raw results (JSON per query) |
| `search_results/` | Historical search results |
| `scan_logs/` | Scan log archives |

### Site (`job-dashboard-site/`)

| Path | Purpose |
|------|---------|
| `index.html` | **Generated** dashboard (do not edit manually) |
| `netlify.toml` | Netlify config: redirects, functions, headers |
| `netlify/functions/generate-pack.mjs` | On-demand ZIP pack generator (serverless) — **only local Netlify function** |
| `applications/` | Per-role PDFs, cover letters, resumes, pack ZIPs, and markdown sources (1,362 files) |
| `jobs_nonlinkedin_2026-08-08.json` | Copy of job data for deployment |
| `.netlify/` | Netlify build cache + plugins |

**Note:** Other Netlify functions (`gate`, `config`, `jobs`, `ingest`, `status`, `ai-request`) are deployed remotely via Netlify's UI/API and are **not** in the repo. Only `generate-pack.mjs` is source-controlled.

### Other Root Files (context, not core pipeline)

| File | Purpose |
|------|---------|
| `ha-automations.yaml` | Home Assistant automation configs |
| `ha-dashboard-views.yaml` | Home Assistant dashboard views |
| `ha-music-assistant-setup.md` | Music Assistant setup notes |
| `ha_states.json` | HA entity state dump |
| `n8n_*.template.json` | n8n workflow templates (job automation) |
| `N8N_JOB_AUTOMATION_PLAN.md` | n8n automation plan doc |
| `refresh_*.py` | Date-specific data refresh scripts |
| `merge_*.py` | Data merge utilities |
| `_css_block.css` | CSS extraction block |
| `_extract_css.py` | CSS extraction script |
| `AGENTS.md` | Agent configuration (empty) |
| `SOUL.md` | Agent soul file (empty) |
| `MEMORY.md` | Agent memory notes |
| `TOOLS.md` | Local infrastructure & environment |

---

## IT Subcategories (7 lanes)

| Key | Title | Color | Description |
|-----|-------|-------|-------------|
| `cloud-devops` | Cloud & DevOps | `#62d9ff` | Azure, AWS, Kubernetes, Terraform, Docker |
| `security` | Security & Cyber | `#ff6b6b` | SOC, cyber, compliance, penetration testing |
| `m365-identity` | M365, Identity & Endpoint | `#bda7ff` | Entra ID, Intune, MDM, EUC |
| `service-desk` | Service Desk & Support | `#ffc857` | L1/L2/L3, help desk, desktop support |
| `infrastructure-systems` | Infrastructure & Systems | `#61e6a6` | Sysadmin, networking, servers, data centre |
| `software-data` | Software & Data | `#ff8a65` | Software engineering, data, AI/ML |
| `project-management` | Project & IT Management | `#91a7bc` | PM, BA, delivery, agile |

---

## Dashboard Layout

### 4 Main Lanes

1. **Core Infrastructure** — Most relevant to Sam's experience. Uses subcategory lanes.
2. **Local & Practical Roles Near St Kilda** — Service desk, help desk, local IT.
3. **Council, Parks & Outdoor Work** — Council IT, parks, community services.
4. **Technician Roles, Traineeships & Training** — Hands-on trade, NBN, telecom.

### Card Features

- Score badge (% screening match)
- Company, title, location, posted date, source
- Work arrangement (remote/hybrid/onsite)
- LinkedIn verification badge (if source = LinkedIn)
- Audit panel (matched terms + gaps)
- Stage controls (New → Review → Ready → Applied → Interview → Offer → Rejected)
- Document links (résumé PDF, cover letter PDF, email PDF, ZIP pack)
- Copy link button (permalink to role)
- Generate application / AI interview prep buttons

### Stage Persistence

Stages stored in `localStorage` keyed by `role_id` (SHA-256 hash of application route). Persists across page loads without backend.

---

## Netlify API Routes

| Route | Function | Purpose |
|-------|----------|---------|
| `/api/gate` | Password gate | Authentication check |
| `/api/config` | Config | Site configuration |
| `/api/jobs` | Jobs | Job data endpoint |
| `/api/ingest` | Ingest | Job data ingestion |
| `/api/status` | Status | Health check |
| `/api/ai-request` | AI request | AI-powered features |
| `/api/generate-pack` | generate-pack.mjs | On-demand ZIP pack generation |

**Note:** All routes except `/api/generate-pack` are deployed via Netlify's managed functions (not in repo). `generate-pack.mjs` is the only serverless function with source in `netlify/functions/`.

---

## Deployment

### Command
```powershell
cd C:\Users\samlu\.openclaw\workspace\job-dashboard-site
netlify deploy --prod --site 909bff86-27e5-4a34-b09e-bbb6cdc04a39
```

### Post-Deploy Checks
1. HTTP 401 on root (password gate active)
2. Card count matches input JSON job count
3. PDF pack files exist in `applications/`

---

## Seek Scraper (2026-08-22)

**File:** `seek_scraper.py` (12.6KB)

### Capabilities
- **REST API:** Primary method via `https://www.seek.com.au/api/jobsearch/v5/search`
- **GraphQL fallback:** `https://www.seek.com.au/graphql`
- **Playwright browser:** Cloudflare bypass for detail pages
- **SSR fallback:** `__NEXT_DATA__` extraction (if available)

### CLI
```bash
python seek_scraper.py --title "software engineer" --location Sydney --max-results 10 --use-browser
```

### Key Selectors (Playwright DOM extraction)
- `data-automation="jobAdDetails"` — Full job description HTML
- `data-automation="job-detail-title"` — Job title
- `data-automation="advertiser-name"` — Company name
- `data-automation="job-detail-location"` — Location
- `data-automation="job-detail-salary"` — Salary
- `data-automation="job-detail-work-type"` — Work type
- `data-automation="job-detail-classifications"` — Classification
- `a[href^="mailto:"]` — Email addresses (bypasses seek masking)

### Output Schema
Matches the sample format provided by Sam. See `seek_test.json` for examples.

---

## Known Issues & Tech Debt

1. **No `__NEXT_DATA__`** — seek.com.au no longer uses Next.js SSR. DOM extraction via Playwright is the reliable path.
2. **Detail page fields** — Some fields (numApplicants, listedAt, recruiterProfile) only come from the search API, not the detail page.
3. **Rate limiting** — Seek limits to 500 results per unique filtered query. Rotate search terms for larger scrapes.
4. **Cloudflare** — Detail pages blocked from datacenter IPs. Playwright handles this, but adds ~3s per job.
5. **Historical scripts** — Multiple `build_*.py` and `refresh_*.py` variants exist. `build_nonlinkedin_dashboard.py` is the canonical dashboard generator.
6. **Netlify functions not in repo** — Most serverless functions (`gate`, `config`, `jobs`, `ingest`, `status`, `ai-request`) are managed via Netlify UI, making local debugging harder.
7. **applications/ bloat** — 1,362 files including markdown sources, PDFs, emails, and ZIPs. Consider archiving old application materials.

---

## Agent Behavior

When the `job-dashboard` agent is invoked:

1. Read this file first (no need to scan all files).
2. Identify which component needs changes.
3. Make targeted edits.
4. Regenerate `index.html` if dashboard generator was modified.
5. Deploy if requested.
6. **Update this document** if architecture changed.
7. Report: what changed, verification results.

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-08-22 | Verified & updated architecture doc. Updated file sizes (JSON 851KB), added missing root files (generate_dashboard.py, scrape-config.json), expanded pipeline inventory, noted Netlify function deployment model, added known issue #7 | Job Dashboard Agent |
| 2026-08-22 | Added seek_scraper.py with Playwright Cloudflare bypass | Sam |
| 2026-08-22 | Created living architecture document | Job Dashboard Agent |
| 2026-08-22 | Documented 7 IT subcategories and dashboard layout | Job Dashboard Agent |
