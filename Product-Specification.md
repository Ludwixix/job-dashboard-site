Product Specification: Melbourne Job Dashboard1. System Objective & Core VisionThe Melbourne Job Dashboard is an automated job search and application management system designed to eliminate manual friction from the hiring process. The platform aggregates listings across multiple job boards, categorizes them into three distinct employment streams, generates grounded role-tailored application materials using a central Master Résumé, and offers both manual download packs and automated 1-click application workflows.2. Targeted Ingestion StreamsIncoming listings from platforms like Indeed, Glassdoor, Google Jobs, Adzuna, and employer career pages are automatically routed into three dedicated streams:                            ┌──────────────────────────────────┐
                            │    Aggregated Job Sourcing       │
                            │  (Scrapers, RSS, Job Board APIs) │
                            └────────────────┬─────────────────┘
                                             │
             ┌───────────────────────────────┼───────────────────────────────┐
             ▼                               ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│     1. Core IT Roles    │     │ 2. Local "Bridge" Jobs  │     │ 3. Traineeships/Trades  │
│ • Systems Engineering   │     │ • No formal certs       │     │ • Structured training   │
│ • Cloud, Entra ID, M365 │     │ • Casual / Part-Time    │     │ • Telecoms & Cabling    │
│ • Infrastructure/Tier 3 │     │ • Immediate local area  │     │ • Data Centre & HVAC    │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
Stream 1: Core IT & Systems EngineeringMid-level roles matching enterprise infrastructure, Microsoft 365, Azure, Entra ID, Windows Server, PowerShell, automation, and Tier 2/3 systems engineering experience.Stream 2: Local "Bridge" & Casual WorkLow-barrier, casual, or part-time employment within the immediate local area (St Kilda / Balaclava radius) requiring no prerequisite qualifications, designed for flexible interim income.Stream 3: Technical Traineeships & Trade PathwaysEntry-level trade or technician positions offering structured on-the-job training, apprenticeships, or vendor certs across Telecommunications (cabling/fibre), Data Centre operations, and HVAC/mechanical services.3. Master Résumé & Dynamic Tailoring EngineTo guarantee 100% factual accuracy across applications, all tailored outputs derive strictly from a centralized Master Résumé (master_resume.md / career_profile.json).┌─────────────────────────┐       ┌─────────────────────────┐
│     Job Description     │       │      Master Résumé      │
│  (Ingested from Source) │       │ (Single Source of Truth)│
└────────────┬────────────┘       └────────────┬────────────┘
             │                                 │
             └────────────────┬────────────────┘
                              │
                              ▼
               ┌──────────────────────────────┐
               │    LLM / Scoring Pipeline    │
               │ • Extract target keywords    │
               │ • Reorder & emphasize bullet │
               │   points from Master Résumé  │
               │ • Draft targeted cover letter│
               └──────────────┬───────────────┘
                              │
               ┌──────────────┴───────────────┐
               ▼                              ▼
    ┌────────────────────┐          ┌────────────────────┐
    │   Tailored PDF /   │          │ Fit Audit JSON     │
    │   Markdown Résumé  │          │ (Gaps & Checklist) │
    └────────────────────┘          └────────────────────┘
Single Source of Truth: The master document records the full history of verified technical skills, project metrics, tools, certifications, and previous trade experience.Grounded Re-Weighting (No Fabrication): The generation engine reorders, highlights, and contextualizes existing bullet points from the master résumé to align with the specific job description without hallucinating unverified experience.Synchronized Application Packs: For every indexed role, the system pre-compiles:Tailored Résumé (PDF + editable Markdown)Customized Cover Letter (PDF + editable Markdown)Recruiter / Hiring Manager Opening Email draftFit Audit Checklist (matched keywords vs. operational gaps)4. Job Card Interface SpecificationEvery role discovered by the sourcing pipeline renders as a standardized card with complete metadata and dual-action triggers:ElementField / Display TypeDescriptionJob TitleText HeaderSpecific title of the open roleEmployerSubheader / TextCompany or recruiting agency nameDate PostedTimestamp BadgeRelative or absolute posting date (e.g., Posted 2026-08-19)LocationGeographical TagSpecific suburb or regional radius (e.g., Balaclava / St Kilda)Work ModelEnum BadgeOnsite | Hybrid | RemoteOriginal ListingOutbound Link (↗)Direct hyperlink to the original job postingCustom PackDownload Button (⬇)Download link for the tailored résumé, cover letter, and auditAutomate ApplyAction Button (⚡)1-click trigger to dispatch the automated application pipeline5. Application Execution Pipelines                             ┌───────────────────────┐
                             │       Job Card        │
                             └───────────┬───────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
  ┌─────────────────────────────┐                 ┌─────────────────────────────┐
  │     Manual Route (⬇)        │                 │    Automated Route (⚡)      │
  │ • Download custom pack      │                 │ • Authenticated proxy call  │
  │ • Review pre-flight audit   │                 │ • Dispatches n8n pipeline   │
  │ • Submit on company portal  │                 │ • Form autofill / submission│
  └─────────────────────────────┘                 └─────────────────────────────┘
Manual Application Flow:Clicking the custom pack link downloads the generated PDF/Markdown assets. The user reviews the pre-flight checklist (e.g., verifying change windows or on-call rosters) and submits the tailored files directly via the employer's portal.Automated Application Flow:Clicking the automated apply button routes an authenticated request through the serverless proxy (Netlify) to trigger the n8n automation engine, which handles form autofill and submission staging.
