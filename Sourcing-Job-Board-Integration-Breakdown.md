Sourcing & Job Board Integration Breakdown
┌─────────────────────────────────────────────────────────────────────────────┐
│                             SOURCING CHANNELS                               │
├───────────────────┬─────────────────────────────┬───────────────────────────┤
│     PLATFORM      │      INTEGRATION MODE       │    PIPELINE CAPABILITY    │
├───────────────────┼─────────────────────────────┼───────────────────────────┤
│ **Indeed**        │ Automated Ingestion / Feeds │ Full ingest, score, packs │
│ **LinkedIn**      │ Sourced Listings / Webhooks │ Full ingest, score, packs │
│ **SEEK**          │ Search-Only / Direct Links  │ Pre-filtered query routes │
│ **Adzuna / APIs** │ Direct REST API Ingestion   │ Full ingest, score, packs │
│ **Gov & Councils**│ RSS / Direct Scrape Feeds   │ Full ingest, score, packs │
└───────────────────┴─────────────────────────────┴───────────────────────────┘
1. Indeed
Method: Ingested via API/feeds, structured RSS, and scraper nodes.

Capabilities: Extracts full job descriptions, employer names, locations, and posting dates. Automatically feeds into the fit-scoring engine to generate custom résumés, cover letters, and opening emails.

2. LinkedIn
Method: Ingested via targeted feeds, API hooks, and structured search queries.

Capabilities: Parses role details, categorizes them into their relevant stream (IT, Local Casual, or Trade/Traineeship), and compiles custom application packs alongside fit audits.

3. SEEK (The Verification Nuance)
Method: Targeted Search Links & Direct Routing (with optional authenticated session ingestion).

Why: SEEK actively deploys strict anti-bot and Cloudflare human-verification challenges that can block automated headless scrapers.

How the Dashboard Handles It:

Curated Search Routes: The dashboard maintains pre-configured, location- and keyword-filtered SEEK search links so you can launch high-intent searches in one click without being blocked.

Manual URL Ingestion: If you find a role on SEEK, you can paste the URL or job text directly into the dashboard trigger to run the fit-audit and generate the custom application pack.

4. Additional Aggregation Channels
To ensure no roles fall through the cracks, the sourcing engine also pulls from:

Adzuna API: Native API integration with structured metadata for Melbourne and local suburbs.

Google Jobs: Aggregated indexing across hundreds of niche boards and direct company career pages.

Victorian Government & Local Council Boards: Direct feeds for public sector IT, infrastructure, and local council maintenance/traineeship roles.

Glassdoor & Direct Employer Portals: Ingested verified routes for direct company submissions.
