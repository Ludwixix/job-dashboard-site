# MASTER CV DATA SOURCE — Sam Ludwig
Last updated: August 2026
Purpose: This is a structured reference document for an AI agent to draw from when generating a job-specific, tailored CV. It is NOT meant to be sent to an employer as-is — it is a comprehensive data source to select, trim, and reorder from.

---

## HOW TO USE THIS DOCUMENT (Agent Instructions)

1. **Read the target job ad first.** Identify: role title, seniority level, must-have technologies, industry/sector, and tone (corporate/government vs startup/agile).
2. **Select a summary** from the "Summary Variants" section that best matches the role, or blend two.
3. **Select 4–6 technical categories** from "Technical Expertise" that match the job ad's keywords. Do not dump the entire competency list — that's for reference only, not for copy-paste into a 1–2 page CV.
4. **For each role in Experience**, select 3–5 bullet points (not all of them) that best match the target job. Each bullet below is tagged with `[theme: ...]` to help you match relevant ones quickly.
5. **Default output length**: 1–2 pages for a standard corporate/government application, matching the style of the "PDF Reference Version" at the end of this doc. Only go longer if the user explicitly asks for a detailed/technical CV.
6. **Do not fabricate metrics, dates, or client names.** Only use what's in this document.
7. **Flag date conflicts.** Two prior CV versions gave different employment dates for Capgemini/Dept. of Education, Australia Post, and St John of God. Use the dates in the "Experience" section below (marked as authoritative) unless the user has since confirmed different dates — and mention to the user if this is the first time tailoring a CV in a session, so they can double check before it goes out.
8. **Tone**: technically credible, outcome-focused, no generic filler adjectives without a metric or specific system attached.

---

## CONTACT / HEADER BLOCK (always include, standard format)

```
Sam Ludwig — [Insert Target Role Title Here]
Melbourne, VIC | 0405 993 245 | sam.ludwig@gmail.com
linkedin.com/in/sam-ludwig | samludwig.au | github.com/Ludwixix
```

Additional (include only if relevant to the role, e.g. government/security roles):
- Citizenship: Australian Citizen
- Security Clearance: No current clearance. Eligible and willing to apply (Baseline / NV1).
- Work Rights: Unrestricted (Australian Citizen)
- Preferred Engagement: Permanent, Contract, Fixed-Term

---

## SUMMARY VARIANTS (pick/blend based on role)

**A. Infrastructure & Cloud Engineer angle:**
Infrastructure and M365 Engineer with 6+ years bridging physical infrastructure and large-scale hybrid cloud environments. Trusted by Victoria Police, Transurban, and the Department of Education Victoria to manage complex infrastructure and drive automation-focused outcomes. Specialist in Microsoft 365 (Exchange, Intune, SharePoint, Teams, Entra ID), PowerShell automation, and endpoint management across environments supporting 660,000+ users.

**B. Automation/DevOps angle:**
Infrastructure engineer with a strong automation bias — has shipped 5+ production automation tools (PowerShell, Python, JavaScript) that eliminated manual toil across ServiceNow, SharePoint, and Exchange environments at enterprise and government scale. Comfortable across the full stack from CI/CD pipelines to Layer 1 cabling.

**C. M365 / Modern Workplace angle:**
M365 Engineer with deep expertise across SharePoint Online, Exchange Hybrid, Teams, Entra ID, and Intune. Managed the largest SharePoint farm in the Southern Hemisphere (660,000+ users) and led enterprise-wide endpoint migrations in zero-tolerance environments (live hospital networks). Strong stakeholder-facing skills, from client workshops to clinical staff hypercare support.

**D. Support/Escalation (L2/L3) angle:**
IT support engineer with progressive experience from field telecommunications through to Tier-3 escalation ownership for a 660,000+ user M365 environment. Track record of >90% SLA resolution across high-volume queues (40+ concurrent tickets), and of engineering automation that permanently removes recurring incident classes rather than just resolving tickets.

**E. Security/Compliance angle:**
Infrastructure engineer with applied experience in identity security and compliance automation — built and ran a PnP PowerShell system auditing MFA compliance across 200+ sensitive SharePoint sites for a state government department, aligned cloud adoption work to the ACSC Essential 8 maturity model, and holds AZ-104/AZ-900.

---

## TECHNICAL EXPERTISE (categorised — pick relevant subset per role)

**Cloud & Microsoft 365**
SharePoint Online/Server, SPFx, PnP PowerShell, Term Store, Exchange Online/Hybrid, EOP, ATP, Teams (Admin Center, Voice, Policies, Guest Access), OneDrive for Business, Entra ID (Azure AD), Azure AD Connect, ADFS, PHS, PTA, Seamless SSO, Dynamic Groups, Azure VMs/Functions/Automation/DevOps, Power Automate, Power Apps, Power BI

**Identity & Security**
Entra ID, ADFS, Conditional Access, MFA enforcement strategy, SSPR, Identity Protection (risk-based policies), Exchange Online Protection, DKIM/SPF/DMARC, Microsoft Purview (DLP, retention, eDiscovery, litigation hold), ACSC Essential 8, NIST, ISO 27001 compliance

**Endpoint Management**
Microsoft Intune (MDM/MAM), Windows Autopilot, SCCM, MDT, SOE design (Windows 10/11 Enterprise, Group Policy), full device lifecycle management, Jamf Pro (macOS), Android Enterprise, iOS MDM

**Infrastructure & Data Centre**
VMware vSphere (ESXi, vCenter), Hyper-V, Windows Server 2012R2–2022, Active Directory Domain Services, DNS, DHCP, Certificate Services, Layer 1 physical cabling (fibre/copper), structured cabling standards, HVAC/thermal management, SAN/NAS, DFS

**Automation & DevOps**
PowerShell 5.1/7 (Expert), PnP PowerShell, Exchange Online Management, Graph API, Python 3 (Selenium, Tkinter, web scraping), JavaScript/TypeScript/React/Node.js, SPFx, Azure DevOps Pipelines, Git/GitHub, REST APIs/OAuth, browser automation (Tampermonkey/Greasemonkey, DOM manipulation)

**Service Management & Operations**
ITIL 4 (incident/problem/change/SLA management), ServiceNow (advanced), Zendesk, Jira Service Management, Splunk, KQL, Azure Monitor, RCA reporting, runbooks, high-volume queue management (40+ concurrent, >90% SLA)

**Other Platforms**
Google Workspace (Admin Console, directory sync), Sharegate, AvePoint, BitTitan MigrationWiz, SPMT, Mover.io, Microsoft Defender (O365/Endpoint), SQL Server, Agile/Scrum/Kanban/Waterfall

---

## EXPERIENCE (authoritative dates — from Emperor CV master record)

### L2/L3 Technical Support Engineer
**Australia Post (via Capgemini)** | Feb 2026 – Jun 2026 | Melbourne, VIC

- [theme: automation, servicenow] Engineered a custom keystroke injection automation solution within ServiceNow to work around locked-down system access controls — programmatically created/modified ITSM tickets, eliminating hundreds of hours of manual data entry per month.
- [theme: endpoint, autopilot, lifecycle] Managed full endpoint lifecycle: OS migrations (Win10→11), SOE imaging, Autopilot/UEM enrolment, and compliant disposal with data sanitisation.
- [theme: support, service desk] Delivered L1/L2 face-to-endpoint and remote support at the MyITHub service centre: device repair, hardware diagnostics, loan device management, new employee provisioning.
- [theme: process improvement] Contributed to a ServiceNow Stock Accessories module implementation and monthly stock watermark reviews to improve inventory visibility and SLA tracking.
- [theme: self-service, ux] Played a key role in rolling out a self-help kiosk programme (KB access, password resets, ticket logging, appointment booking), reducing walk-in volume.
- [theme: escalation] Acted as primary escalation point for complex infrastructure faults, working with L3 teams to drive incidents to permanent resolution.

### Endpoint Migration Engineer
**St John of God Health Care** | Oct 2025 – Jan 2026 | Melbourne, VIC

- [theme: endpoint, autopilot, healthcare, zero-disruption] Led a Windows 11 enterprise migration across 100+ clinical endpoints, maintaining 100% adherence to Autopilot provisioning and SOE standards in a live, patient-facing environment.
- [theme: lifecycle, intune] Managed full migration lifecycle: hardware prep, Autopilot enrolment, Intune policy application, post-deployment validation, user handoff and training.
- [theme: stakeholder management, clinical] Served as primary technical liaison between clinical staff and the engineering team, translating technical issues for medical/nursing staff with zero tolerance for disruption.
- [theme: hypercare, clinical systems] Provided intensive hypercare support post-migration, resolving compatibility issues across EMR, PACS diagnostic imaging, clinical administration tools, and patient monitoring interfaces — zero disruption to patient care.

### Senior Managed Services Engineer (Consultant to Department of Education Victoria)
**Capgemini** | December 2021 – 2023 | Melbourne, VIC

- [theme: scale, sharepoint, governance] Managed the largest SharePoint farm in the Southern Hemisphere — 660,000+ active users, 1,000+ site collections — consistently achieving 99.9% uptime in a government SLA environment.
- [theme: escalation, L3, RCA] Served as the ultimate Tier-3 escalation point across the M365 ecosystem (SharePoint Online, Exchange Online, Teams, Google Workspace). Led RCA investigations resulting in a documented 15% reduction in repeat incidents over 12 months.
- [theme: automation, security, compliance, flagship] **Flagship project:** Engineered a PnP PowerShell automation solution to audit and enforce MFA compliance across 200+ sensitive SharePoint sites — automated discovery, membership/MFA status checks, structured compliance reporting — eliminating a previously manual, month-long audit cycle.
- [theme: identity, hybrid] Managed sync across three identity platforms (on-prem AD, Entra ID, Google Workspace), resolving identity conflicts and sync/authentication failures to maintain seamless SSO department-wide.
- [theme: exchange, teams, messaging] Administered Exchange Hybrid and Microsoft Teams, resolving complex mail-flow routing, calendar/federation issues, and cross-tenant collaboration scenarios.
- [theme: cloud adoption, security framework] Spearheaded Azure cloud adoption, migrating legacy on-prem workloads to Azure IaaS/PaaS, aligned to the ACSC Essential 8 maturity model.
- [theme: automation, tooling, servicenow] Built a production-grade workload distribution engine (Tampermonkey + ServiceNow integration) using live M365 presence data to auto-recommend ticket assignments — adopted as a standard team tool.
- [theme: documentation, knowledge management] Produced as-built documentation, RCA reports, and runbooks; built a searchable knowledge base that cut recurring-incident resolution time and improved onboarding.
- [theme: operations, SLA] Managed 40+ concurrent tickets in a high-volume government queue, consistently achieving >90% SLA resolution.

### Application Support Engineer
**Knosys** | December 2020 – December 2021 | Melbourne, VIC

- [theme: L3 support, SaaS] Delivered expert L3 application support for the GreenOrbit enterprise intranet platform, achieving 95% SLA resolution across clients including Cotton On, Harvey Norman, and Healthscope.
- [theme: automation, efficiency] Engineered a PowerShell automation solution that cut manual data compilation during cloud migrations by 87% (2 hours → 15 minutes per batch), saving 10+ hours/month.
- [theme: automation, patching] Developed Python/PowerShell scripts to standardise system patching, reducing manual patching effort by 20%.
- [theme: cloud migration, documentation] Contributed to platform upgrades and an AWS migration; authored RCA documentation that became the standing reference for future upgrade cycles.
- [theme: diagnostics, database] Diagnosed application-layer issues including SQL deadlocks, API integration errors/timeouts, front-end rendering defects, and auth/authorisation config — working directly with developers on code-level fixes.

### SharePoint Developer
**Engage Squared** | March 2018 – December 2020 | Melbourne, VIC

- [theme: delivery, sharepoint, enterprise clients] Architected and delivered 5+ bespoke SharePoint Online intranet solutions for Victoria Police, Transurban, and Cimic Group using custom SPFx components (React/TypeScript).
- [theme: CI/CD, devops] Implemented full CI/CD pipelines (Azure DevOps, Git), achieving a 25% reduction in deployment cycle times.
- [theme: migration, governance] Led legacy on-prem to M365 migrations (Sharegate, SPMT), including permission restructuring and ISO 27001-aligned governance frameworks.
- [theme: stakeholder, adoption] Facilitated client-facing technical workshops driving a 20% increase in enterprise adoption of new M365 features.
- [theme: agile] Collaborated in a cross-functional Agile/Scrum delivery model (sprint planning, backlog refinement, retros, pair programming).
- [theme: support] Provided L2/L3 production support and built runbooks/KB articles for client IT teams.

### Telecommunications Technician
**National Broadband Network (NBN)** | October 2016 – November 2017 | Melbourne, VIC

- [theme: layer1, physical infrastructure] Executed Layer 1 telecommunications deployments — fibre and copper structured cabling — across residential, commercial, and multi-dwelling environments.
- [theme: diagnostics, fieldwork] Performed fault-finding and hardware troubleshooting at the physical and data link layers.
- [theme: installation] Installed and maintained NTDs, routers, and customer premises equipment.
- [theme: site assessment] Conducted site surveys for optimal cable routing and equipment placement.

### HVAC Service Technician
**PolaAir** | 2017 | Melbourne, VIC
*(Use only for roles where "hands-on diagnostic background" or "career progression story" adds value — otherwise omit or reduce to one line.)*

- [theme: diagnostics, trade background] Installed, maintained, and repaired commercial HVAC systems; developed systematic mechanical/electrical fault-finding later applied to IT incident resolution and RCA methodology.

---

## EDUCATION & CERTIFICATIONS

**Certifications**
- Microsoft Certified: Azure Administrator Associate (AZ-104) — 2025
- Microsoft Certified: Azure Fundamentals (AZ-900) — 2022
- ITIL 4 Foundation (AXELOS) — 2025

Note: an earlier CV draft also listed "Certified Scrum Master (CSM)" — this does **not** appear in the master record. Do not include it unless the user confirms it's a real, current credential.

**Education**
- Diploma of Information Technology — Coder Academy, Melbourne, VIC — 2019
- Web Development Fast Track Bootcamp — Coder Academy, Melbourne, VIC — 2018

**Vocational / Trade Qualifications — Telecommunications (verified via USI-authenticated transcript)**

Source of record: Authenticated VET Transcript, National VET Provider Collection (USI), generated 12 Aug 2026. All units below show outcome "CA" (Competency Achieved). These directly underpin the NBN Telecommunications Technician role and are strong evidence for any role emphasising Layer 1/physical infrastructure, cabling, or telecom compliance — use selectively, not in full, for non-telecom roles.

*Provider: Blue Sky Academy (RTO 121689), 2017:*
- Use Optical and Radio Frequency Measuring Instruments (ICTBWN305)
- Install Telecommunications Network Equipment (ICTTEN302)
- Construct Aerial Cable Supports (ICTCBL309)
- Install Aerial Cable (ICTCBL310)
- Locate and Identify Cable System Faults (ICTCBL306)
- Install a Cable Lead-In (ICTCBL220)
- Install, Maintain and Modify Customer Premises Communications Cabling: ACMA Restricted Rule (ICTCBL236)
- Perform Restricted Customer Premises Broadband Cabling Work: ACMA Restricted Rule (ICTCMP202)
- Use Electrical Skills in Telecommunications Work (ICTTEN201)
- Use Hand and Power Tools (ICTTEN202)
- Implement and Monitor Environmentally Sustainable Work Practices (BSBSUS401)
- Follow Work Health and Safety and Environmental Policy and Procedures (ICTWHS204)
- Install and Terminate Coaxial Cable (ICTCBL303)
- Install, Maintain and Modify Customer Premises Communications Cabling: ACMA Open Rule (ICTCBL237)
- Install a Complex Digital Reception System (ICTDRE303)
- Install and Test Internet Protocol Devices in Convergence Networks (ICTTEN207)

*Provider: Pinnacle Height Safety Pty Ltd (RTO 40496), 2017:*
- Provide Telecommunications Services Safely on Roofs (ICTWHS201)
- Work Safely at Heights (RIIWHS204D)

*Provider: RSA Express Pty Ltd (RTO 40592), 2016:*
- Work Safely in the Construction Industry (CPCCOHS1001A)

**Agent guidance:** For telecom/field-technician/network cabling roles, summarise this block as something like *"Nationally accredited (ACMA-compliant) telecommunications cabling qualifications, including aerial and customer-premises cabling, fault-finding, and Working at Heights/Construction Industry safety certification (Blue Sky Academy / RTO 121689, 2016–2017)"* rather than listing every unit code — the full list above is reference data, not CV-ready copy. For non-technical or purely corporate M365/cloud roles, omit this section entirely or reduce it to a single line ("underlying trade background in ACMA-compliant telecommunications cabling").

---

## KEY PROJECTS (use 1–3, matched to role; include GitHub links for technical/dev-leaning roles)

| Project | One-line pitch | Stack | Link |
|---|---|---|---|
| YellowSnow | Browser extension integrating M365 presence data with ServiceNow ticket queues to auto-recommend assignments; adopted as standard team tool | JavaScript, Tampermonkey, REST APIs | github.com/Ludwixix/YellowSnow |
| PySPO Tool | GUI enabling Tier-1 staff to safely run PowerShell diagnostics against Exchange/Teams without PowerShell expertise | Python, Tkinter, PowerShell | github.com/Ludwixix/pyspo-tool |
| JobGobblin | Boolean-search job board scraper (LinkedIn/Seek/Indeed) with structured extraction and dedup | Python, Selenium | github.com/Ludwixix/JobGobblin |
| MFA Compliance Automation | PnP PowerShell system auditing MFA compliance across 200+ sensitive SharePoint sites, automated reporting | PowerShell, PnP, Graph API | (internal — no public repo) |

---

## CAREER METRICS BANK (pull individual stats to support relevant bullets — don't dump the whole table into a CV)

- 660,000+ users / 1,000+ site collections managed (largest SharePoint farm in the Southern Hemisphere)
- 99.9% SharePoint uptime over multi-year production operations
- 87% reduction in M365 migration processing time (2 hrs → 15 min)
- 25% reduction in deployment cycle time via CI/CD
- 15% reduction in repeat incidents via systematic RCA
- 95% SLA resolution rate (L3, Knosys)
- >90% SLA resolution rate (40+ concurrent tickets, Capgemini)
- 100+ clinical endpoints migrated with zero patient care disruption
- 5+ bespoke SharePoint solutions delivered (Victoria Police, Transurban, Cimic Group)
- 20% increase in M365 adoption via client workshops

---

## ENTERPRISE CLIENT PORTFOLIO (name-drop selectively based on target employer's sector)

| Organisation | Sector | Engagement | Work |
|---|---|---|---|
| Australia Post | Government enterprise | Consultancy (Capgemini) | L2/L3 support, automation, endpoint lifecycle |
| St John of God Health Care | Healthcare / Private | Project | Windows 11 migration, Autopilot |
| Department of Education Victoria | State Government | Consultancy (Capgemini) | SharePoint ops, M365 engineering, automation, L3 |
| Victoria Police | State Government | Client (Engage Squared) | SharePoint intranet |
| Transurban | Infrastructure / Private | Client (Engage Squared) | SharePoint intranet |
| Cimic Group | Construction / Private | Client (Engage Squared) | SharePoint intranet |
| Cotton On | Retail / Private | Client (Knosys) | L3 application support |
| Harvey Norman | Retail / Private | Client (Knosys) | L3 application support |
| Healthscope | Healthcare / Private | Client (Knosys) | L3 application support |

---

## ROLE TARGETING MATRIX

| Role Category | Emphasise | Target Audience |
|---|---|---|
| Senior Infrastructure / Cloud Engineer | Azure, M365, hybrid identity, PowerShell automation, ACSC Essential 8 | Enterprise IT, government, MSPs |
| Modern Workplace / M365 Engineer | SharePoint, Teams, Exchange, Intune, Autopilot, adoption strategy | Consulting firms, enterprise IT |
| DevOps / Automation Engineer | CI/CD, PowerShell/Python, Azure DevOps, ServiceNow integration, API dev | Tech-forward orgs |
| L3 Support / Systems Administrator | Escalation, RCA, SLA delivery, documentation | MSPs, enterprise service desks |
| Application Support Engineer | SaaS platforms, API integrations, cloud migrations, DB diagnostics | SaaS companies, enterprise IT |
| Endpoint / EUC Engineer | Intune, Autopilot, SCCM, SOE design, Windows 11, device lifecycle | Enterprise IT, healthcare, education |
| Security / Compliance Engineer | Conditional Access, MFA, ACSC Essential 8, Purview, compliance automation | Government, regulated industries |
| SharePoint / M365 Developer | SPFx, React, TypeScript, PnP PowerShell, Azure DevOps, CI/CD | Consulting firms, enterprise IT |

---

## DATE DISCREPANCY LOG (resolve with user before final submission of any CV)

An earlier tailored PDF version of this CV used different employment dates than the master record:

- Capgemini / Dept. of Education: PDF said "Dec 2021 – Present"; master record says "Dec 2021 – 2023"
- Australia Post: PDF said "2023 – 2024"; master record says "Feb 2026 – Jun 2026"
- St John of God: PDF said "2023"; master record says "Oct 2025 – Jan 2026"

**Action for agent:** default to the master record dates above. If generating a CV for a live application, prompt the user to confirm current employment status and exact dates before sending, since accuracy here matters for reference checks.

---

## REFERENCES

Available upon request. Referees available from Capgemini, Knosys, Engage Squared, and St John of God Health Care.
