# n8n Job Automation Plan

## Recommended path

Use a source adapter and a small persistence API instead of writing directly to the static Netlify bundle.

1. **Primary discovery:** Adzuna API, JobSpy/Indeed where permitted, and direct employer ATS feeds.
2. **SEEK pilot:** Apify SEEK actor only after reviewing SEEK terms, the actor’s licence, data-retention rules, and the expected request volume. Keep it isolated, rate-limited, monitored, and labelled as `community_scraper`.
3. **Do not use Reed for Melbourne coverage:** Reed is UK-focused and doesn’t add useful Australian coverage for this dashboard.
4. **Orchestration:** n8n scheduled workflow calls each adapter, normalises records, deduplicates them, asks an AI model for structured screening metadata, then POSTs records to a persistence API.
5. **Dashboard:** Netlify serves the UI. A backend stores jobs, statuses, generated-document metadata, and audit history. Netlify Blobs, Supabase, or a small FastAPI service are suitable persistence options. Don’t put API keys in browser JavaScript.

## Source comparison

| Option | Melbourne/SEEK value | Recommendation | Main risk |
|---|---|---|---|
| Adzuna API | Good aggregator coverage and structured fields | **Start here** | Coverage and API quota vary by market |
| Apify SEEK actor | Direct SEEK extraction is technically possible | **Small pilot only** | Community actor, changing anti-bot behaviour, SEEK terms, cost, and reliability |
| Reed | Primarily UK job market | Don’t prioritise | Little Australian value |
| Direct employer ATS feeds | High-quality source and direct application route | Add continuously | One adapter per employer or ATS |
| JobSpy/Indeed | Already usable in the current workflow | Keep as a source where permitted | Scraping stability and board terms |
| Bright Data | Broad paid data infrastructure | Consider only at higher volume | Cost and vendor dependency |

## n8n workflows

### A. Daily sourcing

`Manual test trigger → HTTP Request (Adzuna) → Code: normalise and deduplicate → POST /api/ingest → review response → enable daily schedule`

Use `source`, `source_record_id`, `canonical_url`, `first_seen_at`, `last_seen_at`, `is_expired`, and `application_route` on every record.

### B. Generate application

Dashboard button → signed-in Supabase session → authenticated `/api/ai-request` Netlify function → n8n webhook → validate role ID and current job record → load verified résumé profile → AI drafting step → generate Markdown and PDF in a controlled worker → save document metadata → return links. Webhook URLs and tokens stay in Netlify server-side environment variables; the browser never receives them.

Document generation must not move a role to `Applied`. The safe automatic transition is `New` → `Review` or `Ready`. `Applied` requires Sam’s explicit confirmation.

### C. Interview preparation

Dashboard button → signed-in Supabase session → authenticated `/api/ai-request` Netlify function → n8n webhook → load job description, résumé version, and audit → AI produces questions, technical topics, evidence prompts, and gaps → save as a preparation record → return a dashboard link.

### D. Mailbox status detection

Gmail trigger → strict sender/content classifier → propose a status update → require review for ambiguous messages. Don’t automatically send mail, submit applications, or mark a job as `Interview` from weak evidence.

## Match scoring contract

The model should return JSON, not free text:

```json
{
  "score": 1,
  "fit": "Strong fit | Possible fit | Stretch | Insufficient data",
  "matched_terms": [],
  "evidence": [],
  "gaps": [],
  "requirements_to_confirm": [],
  "confidence": 0.0,
  "needs_human_review": true
}
```

Score meanings:

- `1`: insufficient data or poor fit
- `2`: substantial gaps
- `3`: plausible fit with material gaps
- `4`: strong fit
- `5`: exceptional fit with verified evidence

The score is a prioritisation aid, not an ATS guarantee. The dashboard may display it as a screening score only.

## Persistence API contract

### `POST /api/ingest`

Accepts `{ "jobs": [...] }` or an array of normalised jobs. The server must validate fields, reject LinkedIn records, deduplicate by `canonical_url` and source ID, preserve audit history, and never overwrite a manually changed status without an explicit action.

### `POST /api/jobs/:id/status`

Accepts `{ "status": "Review" }`. Require authentication. Keep a timestamped status history.

### `POST /api/applications/generate`

Accepts `{ "job_id": "...", "document_types": ["resume", "cover_letter", "opening_email"] }`. This creates a draft request only. It must not submit anything externally.

### `POST /api/interview-prep`

Accepts `{ "job_id": "...", "resume_version": "..." }` and returns or stores structured preparation material.

## Credentials still required

No external credentials were added automatically. Production activation needs:

- Adzuna application ID and API key
- Apify token and an approved SEEK actor
- n8n base URL and webhook authentication secret
- Backend database or Netlify Blobs credentials
- OpenRouter or another approved model credential
- Gmail OAuth only if mailbox status detection is enabled

Keep all of these in n8n/server credential storage. Never commit them, place them in the static site, or put them in the dashboard URL.

## Current implementation

The static dashboard now includes:

- Browser-local Kanban status controls: New, Review, Ready, Applied, Interview, Offer, and Rejected
- AI interview-prep and application-generation controls that remain inert until the signed-in server-side n8n webhooks are configured
- Role IDs and structured role data embedded for a future authenticated backend
- A documented separation between draft generation and the explicit application-confirmation step

Browser-local status is not a shared database. Configure the backend before relying on it across devices.

Importable, inactive workflow templates are included at `n8n_adzuna_cloud_workflow.template.json` for n8n Cloud, `n8n_adzuna_ingestion_workflow.template.json` for self-hosted n8n, and `n8n_job_sourcing_workflow.template.json` for the combined Adzuna plus disabled SEEK pilot. The Cloud template uses n8n project variables through `$vars`; the self-hosted template uses `$env`. All templates use Adzuna sourcing, normalisation, LinkedIn exclusion, canonical URL deduplication, and the protected `/api/ingest` batch endpoint. None is connected to an account or active schedule.
