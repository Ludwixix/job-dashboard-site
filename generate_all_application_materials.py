from pathlib import Path
import json
import re
from collections import Counter
from datetime import datetime

ROOT = Path(__file__).parent
APP = ROOT / "applications"
AUDITS = ROOT / "application_audits"
DATA_PATH = ROOT / "scrapers" / "jobs_combined.json"
MASTER = ROOT / "resume.md"

APP.mkdir(exist_ok=True)
AUDITS.mkdir(exist_ok=True)
master = MASTER.read_text(encoding="utf-8")
for required in ("Sam Ludwig", "0405 993 245", "sam.ludwig@gmail.com", "Australian Citizen"):
    if required not in master:
        raise RuntimeError(f"Master résumé is missing required verified source text: {required}")

data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

ALL_ROLE_RECORDS = list(data.get("jobs", []))
for _section_roles in data.get("sections", {}).values():
    ALL_ROLE_RECORDS.extend(_section_roles)

DIRECT_ROLE_ADDITIONS = [
    {
        "rank": 0,
        "score": 93,
        "company": "Victorian Institute of Teaching",
        "title": "Senior Cloud Engineer",
        "location": "Melbourne CBD and inner metro suburbs",
        "posted": "2026-08-03",
        "source": "Careers Vic",
        "url": "https://www.careers.vic.gov.au/job/senior-cloud-engineer-77733",
        "remote": False,
        "why": "Direct Victorian Government career-page route for an ongoing Melbourne Senior Cloud Engineer role. The listing identifies Victorian Institute of Teaching, Melbourne CBD and inner metro suburbs, reference VG/1938562, and a salary range of $118,058–$129,273.",
        "tags": ["Direct government", "Azure", "Microsoft 365", "Cloud engineering"],
        "status": "Direct government listing",
        "application_route": "https://www.careers.vic.gov.au/job/senior-cloud-engineer-77733",
        "application_route_type": "Direct government route",
        "listing_verification": "Current Careers Vic search result verified the individual listing and role reference on August 10, 2026; confirm closing status and exact requirements before applying.",
    },
    {
        "rank": 0,
        "score": 91,
        "company": "First Focus IT",
        "title": "Tech Support roles",
        "location": "Melbourne, VIC",
        "posted": "2026-08-07",
        "source": "Indeed",
        "url": "https://au.indeed.com/viewjob?jk=b4f4a51940b29ba4",
        "remote": False,
        "why": "Current individual Indeed listing for Microsoft-focused technical support covering Azure, Active Directory, Outlook, troubleshooting, and customer-facing service operations.",
        "tags": ["Microsoft support", "Azure", "Active Directory", "Customer service"],
        "status": "Individual listing",
        "application_route": "https://au.indeed.com/viewjob?jk=b4f4a51940b29ba4",
        "application_route_type": "Indeed listing",
        "listing_verification": "Individual Indeed listing returned in the August 10, 2026 non-LinkedIn search; confirm the employer route and availability before applying.",
    },
    {
        "rank": 0,
        "score": 89,
        "company": "Converged Medical Solutions",
        "title": "Computer Network and Systems Engineer",
        "location": "Carrum Downs, VIC / remote available",
        "posted": "2026-08-03",
        "source": "Indeed",
        "url": "https://au.indeed.com/viewjob?jk=32d96bb2c221a5a9",
        "remote": True,
        "why": "Individual Indeed listing from a managed services provider specialising in cybersecurity and Microsoft 365 for healthcare, government, and commercial organisations across Australia.",
        "tags": ["Microsoft 365", "Managed services", "Healthcare technology", "Remote available"],
        "status": "Individual listing",
        "application_route": "https://au.indeed.com/viewjob?jk=32d96bb2c221a5a9",
        "application_route_type": "Indeed listing",
        "listing_verification": "Individual Indeed listing returned in the August 10, 2026 non-LinkedIn search; confirm the full description, location, and employer route before applying.",
    },
    {
        "rank": 0,
        "score": 87,
        "company": "FUJIFILM MicroChannel",
        "title": "Microsoft Cloud Solutions Consultant",
        "location": "Melbourne, VIC / hybrid",
        "posted": "2026-07-28",
        "source": "Indeed",
        "url": "https://au.indeed.com/viewjob?jk=6de2dc4817476357",
        "remote": True,
        "why": "Individual Indeed listing for designing, implementing, and supporting Microsoft Azure cloud solutions for customers, with a hybrid Melbourne arrangement and an established Microsoft consultancy context.",
        "tags": ["Azure", "Microsoft cloud", "Consulting", "Hybrid"],
        "status": "Individual listing",
        "application_route": "https://au.indeed.com/viewjob?jk=6de2dc4817476357",
        "application_route_type": "Indeed listing",
        "listing_verification": "Individual Indeed listing returned in the August 10, 2026 non-LinkedIn search; the listing is older, so confirm availability and the direct employer route first.",
    },
    {
        "rank": 0,
        "score": 82,
        "company": "Amazon.com",
        "title": "Data Center IT Support Engineer, MEL - DCO",
        "location": "Melbourne, VIC",
        "posted": "2026-07-27",
        "source": "Indeed",
        "url": "https://au.indeed.com/viewjob?jk=da9892dd900ea21c",
        "remote": False,
        "why": "Individual Indeed listing for IT support inside data-centre infrastructure, with a strong overlap to endpoint support, physical infrastructure, hardware diagnostics, incident response, and disciplined operational procedures.",
        "tags": ["Data centre", "IT support", "Physical infrastructure", "Amazon Web Services"],
        "status": "Individual listing",
        "application_route": "https://au.indeed.com/viewjob?jk=da9892dd900ea21c",
        "application_route_type": "Indeed listing",
        "listing_verification": "Individual Indeed listing returned in the August 10, 2026 non-LinkedIn search; confirm the direct Amazon route, shift pattern, and technical requirements before applying.",
    },
    {
        "rank": 0,
        "score": 94,
        "company": "LGT Wealth Management Australia",
        "title": "Infrastructure Engineer",
        "location": "Melbourne, VIC",
        "posted": "2026-07-25",
        "source": "LGT Careers",
        "url": "https://www.lgtwm.com/au-en/careers/jobs/infrastructure-engineer-364826",
        "remote": False,
        "why": "Direct employer application for a Melbourne infrastructure role covering Windows, Azure, Microsoft 365, Entra ID, PowerShell, incident response, automation, documentation, and production support.",
        "tags": ["Direct employer", "Azure", "Microsoft 365", "Infrastructure operations"],
        "status": "Direct employer listing",
        "application_route": "https://www.lgtwm.com/au-en/careers/jobs/infrastructure-engineer-364826",
        "application_route_type": "Direct employer route",
        "listing_verification": "Direct LGT employer page captured; confirm availability and closing status before applying.",
    },
    {
        "rank": 0,
        "score": 92,
        "company": "Victorian Government",
        "title": "Senior Cloud Engineer",
        "location": "Melbourne CBD and inner metro suburbs",
        "posted": "2026-08-04",
        "source": "Careers Vic",
        "url": "https://www.careers.vic.gov.au/job/senior-cloud-engineer-77733",
        "remote": False,
        "why": "Direct Victorian Government career-page application with a current Melbourne Senior Cloud Engineer listing and an August 17, 2026 closing date shown in search results.",
        "tags": ["Direct government", "Cloud engineering", "Melbourne CBD", "Closing date check"],
        "status": "Direct government listing",
        "application_route": "https://www.careers.vic.gov.au/job/senior-cloud-engineer-77733",
        "application_route_type": "Direct government route",
        "listing_verification": "Careers Vic page found through current web search; confirm the page and closing date before applying.",
    },
]

existing_urls = {role.get("url") for role in data["jobs"]}
for addition in DIRECT_ROLE_ADDITIONS:
    if addition["url"] not in existing_urls:
        addition["rank"] = len(data["jobs"]) + 1
        data["jobs"].append(addition)
        existing_urls.add(addition["url"])

# The August 8 bundle carried this Careers Vic vacancy under a generic
# government label. Keep the individual employer and reference from the
# current listing so the dashboard and application materials stay accurate.
for role in data["jobs"]:
    if role.get("url") == "https://www.careers.vic.gov.au/job/senior-cloud-engineer-77733":
        role.update({
            "company": "Victorian Institute of Teaching",
            "title": "Senior Cloud Engineer",
            "source": "Careers Vic",
            "location": "Melbourne CBD and inner metro suburbs",
            "posted": "2026-08-03",
            "why": "Direct Victorian Government career-page route for an ongoing Melbourne Senior Cloud Engineer role. The listing identifies Victorian Institute of Teaching, Melbourne CBD and inner metro suburbs, reference VG/1938562, and a salary range of $118,058–$129,273.",
            "tags": ["Direct government", "Azure", "Microsoft 365", "Cloud engineering"],
            "status": "Direct government listing",
            "application_route": "https://www.careers.vic.gov.au/job/senior-cloud-engineer-77733",
            "application_route_type": "Direct government route",
            "listing_verification": "Current Careers Vic search result verified the individual listing and role reference on August 10, 2026; confirm closing status and exact requirements before applying.",
        })

data["source_searches"] = [
    {"name": "Indeed", "type": "job board", "url": "https://au.indeed.com/jobs?q=Azure+Microsoft+365+Intune&l=Melbourne+VIC", "status": "individual listings used where available"},
    {"name": "SEEK", "type": "job board", "url": "https://au.seek.com/Melbourne-IT-jobs", "status": "search-only; individual access blocked by human verification"},
    {"name": "Glassdoor", "type": "job board", "url": "https://www.glassdoor.com.au/Job/melbourne-it-jobs-SRCH_IL.0,9_IC2264754_KO10,12.htm", "status": "search route; verify individual listings"},
    {"name": "Jora", "type": "aggregator", "url": "https://au.jora.com/jobs-in-Melbourne-VIC", "status": "search route; verify original employer listing"},
    {"name": "Careers Vic", "type": "government careers", "url": "https://www.careers.vic.gov.au/search", "status": "direct government applications"},
    {"name": "Employer career pages", "type": "direct employer", "url": "https://www.lgtwm.com/au-en/careers/jobs/infrastructure-engineer-364826", "status": "direct employer route; verify listing"},
    {"name": "Victorian Institute of Teaching", "type": "government employer", "url": "https://www.careers.vic.gov.au/job/senior-cloud-engineer-77733", "status": "individual government listing verified in current search"},
    {"name": "Remote Australia", "type": "job board search", "url": "https://au.indeed.com/jobs?q=Azure&l=Remote&fromage=30", "status": "search-only; verify original employer route"},
]

CORE_EMAILS = {
    "Tech Support roles": "The First Focus IT technical support role matches my Microsoft-focused service operations background across Azure, Active Directory, Outlook, endpoint support, troubleshooting, and customer communication.",
    "Computer Network and Systems Engineer": "The Converged Medical Solutions role matches my Microsoft 365, managed-services, healthcare-technology, endpoint, identity, and structured troubleshooting experience.",
    "Microsoft Cloud Solutions Consultant": "The FUJIFILM MicroChannel role matches my Azure, Microsoft 365, identity, automation, enterprise support, and customer-facing technical delivery experience.",
    "Data Center IT Support Engineer, MEL - DCO": "The Amazon data-centre IT support role matches my endpoint support, hardware diagnostics, physical infrastructure, incident response, and disciplined operational-procedure experience.",
    "Infrastructure Engineer": "The LGT Infrastructure Engineer role is a strong match for my experience across Windows, Azure, Microsoft 365, Entra ID, PowerShell automation, incident response, documentation, and production support.",
    "Senior Cloud Engineer": "The Victorian Government Senior Cloud Engineer role matches my Azure, Microsoft 365, identity, automation, enterprise support, and public-sector delivery experience.",
    "End User Computing Support Engineer": "Your Bureau of Meteorology opportunity is a strong match for my endpoint engineering and enterprise support background. I bring hands-on Intune, Autopilot, Windows 10/11, ServiceNow, hardware diagnostics, endpoint lifecycle management and L1/L2/L3 escalation experience.",
    "Infrastructure, Azure & Security Engineer": "Your Infrastructure, Azure and Security Engineer opportunity matches my experience across Azure, Microsoft 365, Entra ID, Intune, Autopilot, PowerShell, SharePoint, Exchange and Essential 8-aligned security work.",
    "Lead EUC Engineer": "Your Lead EUC Engineer opportunity aligns with my endpoint engineering experience across Intune, Autopilot, Windows 10/11, SOE design, compliance, lifecycle management, PowerShell automation and L2/L3 escalation.",
    "Senior Azure Cloud Engineer": "Your Senior Azure Cloud Engineer opportunity aligns with my Azure, Microsoft 365, Entra ID, hybrid identity, PowerShell automation and healthcare-continuity experience.",
    "Infrastructure Engineer": "Your Infrastructure Engineer opportunity matches my experience across Azure, Microsoft 365, Entra ID, Intune, Autopilot, Windows, SharePoint, Exchange, PowerShell and enterprise operations.",
    "EUC Engineer": "Your EUC Engineer opportunity matches my hands-on endpoint delivery across Intune, Autopilot, Windows 10/11, application deployment, compliance, diagnostics and lifecycle management.",
    "End User Services Engineer VIC (Intune MDM, Kandji)": "Your End User Services Engineer opportunity matches my combination of Microsoft 365, Intune, Windows 11, Autopilot, endpoint lifecycle and customer-facing managed-services support.",
    "IT Systems Administrator": "Your IT Systems Administrator opportunity combines the internal IT ownership and systems improvement work that fits my Microsoft 365, Azure, Entra ID, endpoint, ServiceNow and automation background.",
    "Systems Administrator": "Your Systems Administrator opportunity aligns with my experience supporting secure enterprise infrastructure across Windows, Microsoft 365, Entra ID, endpoints, PowerShell and service operations.",
    "Engineer - Modern Workplace (Managed Services)": "Your Modern Workplace Engineer opportunity matches my Microsoft 365, Intune, Autopilot, Windows, Entra ID, automation and managed-services escalation experience.",
    "Cloud Engineer (Level 2)": "Your Level 2 Cloud Engineer opportunity aligns with my Azure, Microsoft 365, Entra ID, endpoint and escalation experience, supported by PowerShell, Graph and ITIL 4 practices.",
    "Service Desk Engineer": "Your Service Desk Engineer opportunity matches my recent L1/L2/L3 support, hardware diagnostics, Windows imaging, Autopilot/UEM, ServiceNow automation and endpoint lifecycle experience. I understand that a short video response is already pending in the existing process."
}

COMMON_EXPERIENCE = [
    "L2/L3 Technical Support Engineer — Australia Post via Capgemini (February 2026–June 2026): hardware diagnostics, Windows imaging, endpoint provisioning, Autopilot/UEM enrolment, inventory, loan devices, compliant disposal and ServiceNow automation.",
    "Endpoint Migration Engineer — St John of God Health Care (October 2025–January 2026): Windows 11 migration across 100+ clinical endpoints using Autopilot, Intune, SOE controls, application validation and hypercare.",
    "Senior Managed Services Engineer — Capgemini, consultant to Department of Education Victoria (December 2021–2023): Tier-3 Microsoft 365, Entra ID, hybrid identity, SharePoint, Exchange, Teams, Azure adoption, PowerShell automation, RCA and runbooks.",
    "Telecommunications Technician — NBN Co (October 2016–November 2017): field-based fibre and copper infrastructure deployment, Layer 1 fault-finding, NTD/router/CPE installation and site assessment.",
    "HVAC Service Technician — PolaAir (2017): commercial HVAC installation, maintenance, repair, systematic fault-finding and multi-site customer service."
]

def employer_name(role):
    company = (role.get("company") or "").strip()
    title = (role.get("title") or "").strip()
    return "your organisation" if not company or company.casefold() == title.casefold() else company

def natural_reason(reason):
    reason = re.sub(r"^Your .*? opportunity (is|matches|aligns with|combines)", r"This role \1", reason)
    replacements = {
        "This is one of the closest matches to my recent endpoint and service-desk work.": "The work is a close match for my recent endpoint and service-desk experience.",
        "This is a deliberate career-change application.": "I’m making a deliberate move into this kind of practical work.",
        "This is a deliberate local career-change application.": "I’m making a deliberate move into local practical work.",
        "This is a local-work transition application.": "I’m looking for a practical local role.",
        "The master résumé does not claim commercial kitchen experience, so this pack focuses only on transferable reliability, service operations, learning ability and structured work.": "I haven’t worked in a commercial kitchen, but I’m used to reliable procedures, service operations, learning new systems and taking responsibility for the work in front of me.",
        "I do not claim a Cert III in Horticulture or prior commercial gardening experience.": "I don’t hold a Cert III in Horticulture and haven’t worked in commercial gardening.",
        "I do not claim parks, conservation or ranger experience, so the position requirements need careful review.": "I haven’t worked in parks, conservation or a ranger role, so I’d want to confirm the position requirements.",
        "I do not claim brushcutter or horticulture qualifications.": "I don’t hold brushcutter or horticulture qualifications.",
        "I do not claim horticultural qualifications, so the role’s exact requirements need verification.": "I don’t hold horticultural qualifications, so I’d want to confirm the role’s exact requirements.",
        "no automotive qualification is claimed.": "I don’t hold an automotive qualification yet.",
        "no panel-beating qualification is claimed.": "I don’t hold a panel-beating qualification yet.",
        "no electrical licence or current electrical apprenticeship stage is claimed.": "I don’t hold an electrical licence and I’m not currently in an electrical apprenticeship.",
        "I do not claim barista, bartending or RSA experience; the application focuses on transferable customer service, calm problem-solving and willingness to learn the venue’s procedures.": "I haven’t worked as a barista or bartender and don’t hold an RSA, but I bring customer service experience, calm problem-solving and a willingness to learn your procedures.",
        "I do not claim housekeeping experience, but I bring disciplined procedures, attention to equipment and inventory, service schedules, documentation and reliable task ownership.": "I haven’t worked in housekeeping, but I’m comfortable following detailed procedures, working to schedules, looking after equipment and taking ownership of a task.",
        "I do not claim prior medical-reception experience.": "I haven’t worked as a medical receptionist before.",
        "The listing is older, so availability must be checked first.": "The listing appears older, so I’d confirm that the position is still available first.",
        "The advertised car and licence requirement must be confirmed.": "I’d need to confirm the advertised car and licence requirement.",
        "The Year 3–4 requirement must be screened first.": "I’d need to confirm the Year 3–4 requirement before applying.",
        "The listing specifies Year 3–4 apprentices, which must be confirmed before applying.": "The listing mentions Year 3–4 apprentices, so I’d confirm that requirement before applying.",
        "The role’s exact requirements need verification.": "I’d want to confirm the role’s exact requirements.",
        "This targeted résumé uses only experience and qualifications recorded in the master résumé. It does not claim role-specific licences, trade certificates, horticulture qualifications, hospitality experience, or clearances that are not recorded there.": "",
    }
    for old, new in replacements.items():
        reason = reason.replace(old, new)
    return reason.strip()

def experience_year(item):
    match = re.search(r"(20\d{2})", item.get("period", ""))
    return int(match.group(1)) if match else 0

CATEGORY = {
    "core": {
        "summary": "Infrastructure and Microsoft 365 engineer with progressive experience across Azure, Entra ID, Intune, Autopilot, Windows, SharePoint, Exchange, PowerShell, ServiceNow and enterprise service operations. Combines hands-on endpoint delivery with Tier-3 escalation, automation, security-aware change and durable documentation.",
        "skills": "Azure · Microsoft 365 · Entra ID · Intune · Windows Autopilot · Windows 10/11 · PowerShell · Microsoft Graph · SharePoint · Exchange Online · Teams · Active Directory · ServiceNow · ITIL 4 · endpoint lifecycle · incident and problem management · RCA · technical documentation · stakeholder communication",
        "experience": [
            "L2/L3 Technical Support Engineer — Australia Post via Capgemini (February 2026–June 2026): hardware diagnostics, Windows imaging, endpoint provisioning, Autopilot/UEM enrolment, inventory, loan devices, compliant disposal and ServiceNow automation.",
            "Endpoint Migration Engineer — St John of God Health Care (October 2025–January 2026): Windows 11 migration across 100+ clinical endpoints using Autopilot, Intune, SOE controls, application validation and hypercare.",
            "Senior Managed Services Engineer — Capgemini, consultant to Department of Education Victoria (December 2021–2023): Tier-3 Microsoft 365, Entra ID, hybrid identity, SharePoint, Exchange, Teams, Azure adoption, PowerShell automation, RCA and runbooks.",
            "Application Support Engineer — Knosys (December 2020–December 2021): L3 application support, PowerShell and Python automation, SQL/API diagnostics, patching and AWS migration support.",
            "SharePoint Developer — Engage Squared (March 2018–December 2020): SharePoint Online, SPFx, React, TypeScript, Azure DevOps, Git, migration, governance and client workshops."
        ],
    },
    "technician": {
        "summary": "Hands-on technician and infrastructure professional combining recent enterprise endpoint support with earlier field telecommunications and HVAC service experience. Interested in structured training, practical troubleshooting and roles where technical capability develops through supervised work.",
        "skills": "Hardware diagnostics · Windows 10/11 · Intune · Autopilot · ServiceNow · Network and Layer 1 fault-finding · Fibre and copper cabling · Data-centre infrastructure fundamentals · HVAC and environmental controls · PowerShell · Technical documentation · Customer support",
        "experience": COMMON_EXPERIENCE,
    },
    "outdoor": {
        "summary": "Field-based infrastructure professional seeking practical outdoor, parks, facilities or council-contracted work. Brings site assessment, physical equipment handling, systematic fault-finding, customer communication, inventory discipline and experience working across Melbourne locations. Any role-specific horticulture, conservation or trade requirements can be discussed directly.",
        "skills": "Field service · Site assessment · Equipment handling · Structured work procedures · Fault-finding · Asset and inventory control · Customer and stakeholder communication · Safety-conscious work practices · Fibre/copper infrastructure · HVAC service · Documentation",
        "experience": COMMON_EXPERIENCE,
    },
    "local": {
        "summary": "Melbourne-based professional seeking a practical local role in St Kilda and nearby suburbs. Brings dependable service-desk operations, customer communication, inventory control, field work, technical problem-solving, documentation and the ability to learn new procedures quickly. Open to a local-work transition and ready to learn the role’s procedures.",
        "skills": "Customer service · Clear communication · Reliable task ownership · Inventory and asset control · Field work · Technical troubleshooting · Process compliance · Documentation · Team collaboration · Fast learning · Microsoft 365 and digital systems",
        "experience": COMMON_EXPERIENCE,
    }
}

TERM_ALIASES = {
    "Azure": ["azure"],
    "Microsoft 365": ["microsoft 365", "m365", "modern workplace"],
    "Entra ID": ["entra", "azure ad", "identity"],
    "Intune": ["intune", "endpoint", "euc", "mdm"],
    "Windows": ["windows", "desktop", "workstation"],
    "Autopilot": ["autopilot"],
    "PowerShell": ["powershell", "automation"],
    "ServiceNow": ["servicenow", "service desk", "service-desk"],
    "SharePoint": ["sharepoint"],
    "Exchange": ["exchange", "mail flow", "email"],
    "Teams": ["teams"],
    "Active Directory": ["active directory", "ad ds", "hybrid identity"],
    "ITIL": ["itil", "incident", "problem management"],
    "Layer 1 networking": ["layer 1", "network", "fibre", "fiber", "copper", "cabling"],
    "HVAC": ["hvac", "air-conditioning", "refrigeration", "thermal", "environmental controls"],
    "Data-centre operations": ["data centre", "data center", "server", "rack", "facilities"],
    "Healthcare technology": ["healthcare", "hospital", "clinical", "medical"],
    "Customer support": ["customer", "user support", "service"],
}

def build_audit(role, category, reason, tags_list):
    target = " ".join([
        role.get("title", ""), role.get("company", ""), role.get("why", ""),
        " ".join(role.get("tags", [])), " ".join(tags_list), reason,
    ]).lower()
    candidate = master.lower()
    matched = [term for term, aliases in TERM_ALIASES.items() if any(alias in target for alias in aliases) and any(alias in candidate for alias in aliases)]
    requested = [term for term, aliases in TERM_ALIASES.items() if any(alias in target for alias in aliases)]
    unsupported = [term for term in requested if term not in matched]

    checks = ["Confirm the listing is still open and review the exact job description."]
    title = role.get("title", "").lower()
    tags_text = " ".join(role.get("tags", [])).lower()
    if "clearance" in target or "government" in target or "security" in target:
        checks.append("Confirm any security-clearance, police-check, or government screening requirement.")
    if "apprent" in title or "trainee" in title or "training" in tags_text:
        checks.append("Confirm the required apprenticeship stage, training pathway, and prior qualification requirements.")
    if any(word in title for word in ("gardener", "ranger", "groundskeeper", "mower", "brushcutting", "parks")):
        checks.append("Confirm horticulture, plant-equipment, physical-capacity, licence, and outdoor-work requirements.")
    if any(word in title for word in ("electrical", "air-conditioning", "refrigeration", "vehicle", "panel beater", "spray painter")):
        checks.append("Confirm the required trade licence, apprenticeship stage, tools, and practical experience.")
    if any(word in title for word in ("barista", "bartender", "cook", "chef", "kitchen")):
        checks.append("Confirm hospitality experience, RSA or food-safety requirements, and roster conditions.")
    if "planogram" in title or "merchand" in title:
        checks.append("Confirm vehicle, driver's-licence, travel, and stock-handling requirements.")
    if "medical receptionist" in title:
        checks.append("Confirm reception, booking-system, privacy, and healthcare-administration requirements.")

    score = int(role.get("score", 0))
    fit = "Strong fit" if score >= 90 else "Good fit" if score >= 80 else "Partial fit"
    return {
        "audit_version": "1.0",
        "fit": fit,
        "score": score,
        "source": role.get("source"),
        "source_url": role.get("url"),
        "application_route": role.get("application_route", role.get("url")),
        "application_route_type": role.get("application_route_type"),
        "listing_verification": role.get("listing_verification"),
        "matched_terms": matched,
        "requested_terms": requested,
        "unsupported_or_unverified_terms": unsupported,
        "requirements_to_confirm": checks,
        "recommendation": "Review the listing and requirements before applying.",
        "human_review": [
            "Check the listing date, closing date, location, roster, and application route.",
            "Read the tailored documents once and edit any wording that doesn’t sound like you.",
            "Confirm every licence, qualification, clearance, vehicle, and work-right requirement.",
            "Submit manually only after your explicit approval.",
        ],
        "source_basis": "Role title, listing metadata, search rationale, and verified candidate profile",
    }

EXPERIENCE_SECTIONS = {
    "core": [
        {
            "heading": "L2/L3 Technical Support Engineer — Australia Post via Capgemini",
            "period": "February 2026–June 2026 · Melbourne, Victoria",
            "bullets": [
                "Delivered L1/L2 endpoint support covering hardware diagnostics, Windows imaging, break-fix work, provisioning, loan devices, accessories, and user access.",
                "Managed Windows 10/11 migrations, standardised SOE builds, Autopilot/UEM enrolment, inventory, and compliant equipment disposal.",
                "Built ServiceNow automation that removed hundreds of hours of repetitive manual data entry each month while working within locked-down endpoint controls.",
                "Supported complex infrastructure faults as an escalation point for L3 engineering teams and documented fixes for repeatable service operations.",
            ],
        },
        {
            "heading": "Endpoint Migration Engineer — St John of God Health Care",
            "period": "October 2025–January 2026 · Melbourne, Victoria",
            "bullets": [
                "Led a Windows 11 migration across more than 100 clinical endpoints using Autopilot, Intune, SOE controls, application validation, and post-deployment hypercare.",
                "Managed hardware preparation, Autopilot enrolment, profile assignment, Intune policy application, compliance checks, user handover, and training.",
                "Worked directly with clinical staff and engineering teams to resolve compatibility issues affecting EMR, diagnostic imaging, and administration systems.",
            ],
        },
        {
            "heading": "Senior Managed Services Engineer — Capgemini, consultant to Department of Education Victoria",
            "period": "December 2021–2023 · Melbourne, Victoria",
            "bullets": [
                "Managed SharePoint Online, Exchange Online, Teams, Entra ID, hybrid identity, Azure, and Google Workspace in a government environment supporting 660,000+ users across 1,000+ site collections.",
                "Acted as a Tier-3 escalation point, led root-cause analysis, and introduced preventive fixes that reduced repeat incidents by 15 percent over 12 months.",
                "Built PnP PowerShell automation to audit and enforce MFA compliance across more than 200 sensitive SharePoint sites, replacing a month-long manual audit cycle.",
                "Supported Azure adoption, legacy remediation, Essential 8-aligned security baselines, mail-flow troubleshooting, identity synchronisation, and operational runbooks.",
            ],
        },
        {
            "heading": "Application Support Engineer — Knosys",
            "period": "December 2020–December 2021 · Melbourne, Victoria",
            "bullets": [
                "Provided L3 support for the GreenOrbit enterprise intranet platform and resolved complex SQL, API, authentication, browser, and Windows Server issues within SLA.",
                "Built PowerShell automation that reduced migration processing time by 87 percent, from two hours to 15 minutes per batch, saving more than 10 hours of manual work each month.",
                "Developed Python and PowerShell patching scripts that reduced manual patching effort by 20 percent and improved cycle consistency.",
            ],
        },
        {
            "heading": "SharePoint Developer — Engage Squared",
            "period": "March 2018–December 2020 · Melbourne, Victoria",
            "bullets": [
                "Delivered enterprise SharePoint Online intranets for Victoria Police, Transurban, and Cimic Group using SPFx, React, TypeScript, and PnP PowerShell.",
                "Implemented Azure DevOps and Git CI/CD pipelines that reduced deployment cycle times by 25 percent.",
                "Led legacy SharePoint migrations, governance work, client workshops, and post-launch L2/L3 support.",
            ],
        },
    ],
    "technician": [
        {
            "heading": "L2/L3 Technical Support Engineer — Australia Post via Capgemini",
            "period": "February 2026–June 2026 · Melbourne, Victoria",
            "bullets": [
                "Diagnosed and repaired Windows endpoint hardware, performed imaging and recovery, provisioned devices, managed loan equipment, and supported users through a high-volume service centre.",
                "Handled Autopilot/UEM enrolment, Windows 10/11 migrations, SOE builds, inventory, accessories, and compliant disposal across the endpoint lifecycle.",
                "Built ServiceNow automation that removed hundreds of hours of repetitive data entry each month.",
            ],
        },
        {
            "heading": "Endpoint Migration Engineer — St John of God Health Care",
            "period": "October 2025–January 2026 · Melbourne, Victoria",
            "bullets": [
                "Migrated more than 100 clinical endpoints to Windows 11 using Autopilot and Intune while supporting live hospital operations.",
                "Prepared hardware, applied policies, checked compliance, validated clinical applications, handed devices to users, and provided hypercare.",
                "Explained technical issues clearly to clinical staff and worked with engineering teams to resolve compatibility problems.",
            ],
        },
        {
            "heading": "Senior Managed Services Engineer — Capgemini",
            "period": "December 2021–2023 · Melbourne, Victoria",
            "bullets": [
                "Supported enterprise infrastructure, endpoint, identity, Microsoft 365, Azure, ServiceNow, documentation, and escalation operations.",
                "Automated repetitive service work with PowerShell and investigated faults through structured root-cause analysis.",
            ],
        },
        {
            "heading": "Telecommunications Technician — NBN Co",
            "period": "October 2016–November 2017 · Melbourne, Victoria",
            "bullets": [
                "Installed and maintained fibre and copper Layer 1 infrastructure across residential, commercial, and multi-dwelling sites.",
                "Performed physical fault-finding, connectivity diagnostics, NTD and router installation, CPE work, and site assessments.",
                "Worked to structured cabling standards while managing customer communication and multiple Melbourne locations.",
            ],
        },
        {
            "heading": "HVAC Service Technician — PolaAir",
            "period": "2017 · Melbourne, Victoria",
            "bullets": [
                "Installed, maintained, and repaired commercial HVAC systems across Melbourne sites.",
                "Used systematic mechanical and electrical fault-finding under time pressure and managed service schedules across multiple customers.",
                "Built practical experience with environmental controls, equipment handling, site work, and customer-facing service.",
            ],
        },
    ],
    "outdoor": [
        {
            "heading": "Telecommunications Technician — NBN Co",
            "period": "October 2016–November 2017 · Melbourne, Victoria",
            "bullets": [
                "Worked across Melbourne sites installing fibre and copper infrastructure, equipment, NTDs, routers, and customer-premises equipment.",
                "Completed site assessments, cable routing, physical fault-finding, equipment handling, and customer communication.",
            ],
        },
        {
            "heading": "HVAC Service Technician — PolaAir",
            "period": "2017 · Melbourne, Victoria",
            "bullets": [
                "Installed, maintained, and repaired commercial HVAC systems across multiple sites.",
                "Managed service schedules, equipment, systematic fault-finding, and customer communication in field conditions.",
            ],
        },
        {
            "heading": "L2/L3 Technical Support Engineer — Australia Post via Capgemini",
            "period": "February 2026–June 2026 · Melbourne, Victoria",
            "bullets": [
                "Managed equipment, inventory, loan devices, accessories, provisioning, repair, and compliant disposal in a high-volume service operation.",
                "Worked through complex faults, followed documented procedures, and coordinated escalations with engineering teams.",
            ],
        },
        {
            "heading": "Endpoint Migration Engineer — St John of God Health Care",
            "period": "October 2025–January 2026 · Melbourne, Victoria",
            "bullets": [
                "Prepared and deployed more than 100 endpoints in live clinical environments, with structured checks, handover, and hypercare.",
                "Worked with staff and technical teams to resolve equipment and application issues without disrupting clinical operations.",
            ],
        },
        {
            "heading": "Senior Managed Services Engineer — Capgemini",
            "period": "December 2021–2023 · Melbourne, Victoria",
            "bullets": [
                "Maintained disciplined asset, incident, documentation, and escalation practices across enterprise infrastructure services.",
                "Used automation and root-cause analysis to reduce repeat work and improve service operations.",
            ],
        },
    ],
    "local": [
        {
            "heading": "L2/L3 Technical Support Engineer — Australia Post via Capgemini",
            "period": "February 2026–June 2026 · Melbourne, Victoria",
            "bullets": [
                "Supported users with hardware, Windows, provisioning, repairs, access, inventory, and service requests in a busy customer-facing environment.",
                "Managed loan devices, accessories, endpoint records, and compliant disposal while keeping work moving against service targets.",
            ],
        },
        {
            "heading": "Endpoint Migration Engineer — St John of God Health Care",
            "period": "October 2025–January 2026 · Melbourne, Victoria",
            "bullets": [
                "Prepared, deployed, and supported more than 100 Windows 11 endpoints in a live hospital environment.",
                "Explained technical issues to staff, coordinated fixes, validated applications, and supported users after handover.",
            ],
        },
        {
            "heading": "Telecommunications Technician — NBN Co",
            "period": "October 2016–November 2017 · Melbourne, Victoria",
            "bullets": [
                "Worked across Melbourne sites installing equipment and physical network infrastructure, assessing work areas, and resolving faults.",
                "Managed customer communication, equipment, structured procedures, and practical work in different environments.",
            ],
        },
        {
            "heading": "HVAC Service Technician — PolaAir",
            "period": "2017 · Melbourne, Victoria",
            "bullets": [
                "Completed scheduled maintenance, repair, equipment handling, and systematic fault-finding across commercial sites.",
                "Managed multiple service jobs and communicated directly with customers about the work required.",
            ],
        },
        {
            "heading": "Senior Managed Services Engineer — Capgemini",
            "period": "December 2021–2023 · Melbourne, Victoria",
            "bullets": [
                "Handled service requests, documentation, stakeholder communication, technical troubleshooting, and process improvement across enterprise systems.",
                "Built automation and knowledge resources that reduced repetitive work and helped teams resolve issues consistently.",
            ],
        },
    ],
}

PROJECTS_BY_CATEGORY = {
    "core": [
        "ServiceNow workload tool — browser extension integrating Microsoft 365 presence data with ServiceNow queues to improve ticket allocation.",
        "M365 diagnostic GUI — Python tool that helps L1 staff run repeatable PowerShell diagnostics against Exchange and Teams.",
    ],
    "technician": [
        "ServiceNow automation — workflow automation for repetitive ticket and endpoint-service tasks.",
    ],
    "outdoor": [],
    "local": [],
}

ROLE_OVERRIDES = {
    "Support Technician": ("technician", "The cardioscan role is a strong local fit for my recent endpoint and service-desk work. The Camberwell location and one-day work-from-home arrangement also make it practical from St Kilda.", ["L1/L2 support", "Windows and endpoint support", "MedTech", "Camberwell"]),
    "IT Support Technician": ("technician", "The Microcel role matches my endpoint support, Windows, hardware and school-technology experience. The part-time structure and nearby Cheltenham or Hawthorn East locations make it a practical option.", ["School technology", "Windows support", "Hardware troubleshooting", "Part-time"]),
    "Technical Assistant/ICT Classroom Support": ("technician", "The education-sector ICT classroom-support role is a strong match for my endpoint deployment, hardware troubleshooting, user communication and school-environment experience.", ["Education", "ICT support", "Windows endpoints", "Southern suburbs"]),
    "Service Desk Technician": ("technician", "The Oakleigh service-desk role matches my recent L1/L2 endpoint support, Windows troubleshooting, incident handling, hardware diagnostics and customer communication experience.", ["Service desk", "Windows support", "Endpoint troubleshooting", "Oakleigh"]),
    "Intermediate Service Desk Technician": ("technician", "The intermediate service-desk role aligns with my L1/L2/L3 support background, Microsoft endpoint experience, troubleshooting discipline and service-operations documentation.", ["Service desk", "L1/L2 support", "Microsoft endpoints", "Remote available"]),
    "Engineering Operations Technician": ("technician", "The data-centre engineering-operations role is a credible practical infrastructure pathway. My endpoint, telecommunications and HVAC backgrounds provide relevant equipment, fault-finding and operational-procedure experience; clearance requirements must be confirmed.", ["Data centre", "Engineering operations", "Infrastructure", "Clearance check"]),
    "Microsoft M365 Systems Administrator": ("core", "The Visy Microsoft 365 Systems Administrator role is a strong match for my enterprise M365, identity, security, compliance, automation and platform-operations background.", ["Microsoft 365", "Security and compliance", "PowerShell", "Platform optimisation"]),
    "Senior Systems Engineer": ("core", "The St Vincent’s Senior Systems Engineer role aligns with my Microsoft cloud, endpoint, identity, healthcare-continuity, escalation and infrastructure-operations experience.", ["Healthcare infrastructure", "Microsoft cloud", "Systems engineering", "Service operations"]),
    "Group Infrastructure Engineer": ("core", "The Icon Group Infrastructure Engineer role matches my enterprise infrastructure, Microsoft 365, Azure, endpoint, automation and transformation experience.", ["Infrastructure", "Modernisation", "Azure", "Transformation"]),
    "Systems Administrator": ("core", "The DYSON GROUP Systems Administrator role matches my Windows, Microsoft 365, endpoint, identity, automation and user-support experience in a permanent operational environment.", ["Systems administration", "Windows", "Microsoft 365", "User support"]),
    "Site Support Senior Technician": ("technician", "The Computershare site-support role matches my endpoint diagnostics, Windows support, user communication, asset handling and enterprise service-operations experience.", ["Site support", "Endpoint support", "Enterprise", "Troubleshooting"]),
    "Senior DevOps Engineer": ("core", "The FMClarity Senior DevOps Engineer role is a stretch toward DevOps, but its Melbourne SaaS environment, cloud operations, automation and service-improvement focus align with my infrastructure background.", ["Cloud operations", "Automation", "SaaS", "Infrastructure"]),
    "Infrastructure Engineer – Telecommunications and IT": ("technician", "The Socia Infrastructure Engineer role connects my NBN telecommunications field background with enterprise infrastructure support across network, compute, storage and service operations.", ["Telecommunications", "Infrastructure", "Networking", "Contract"]),
    "Shift Technician- Air Conditioning & Refrigeration, Data Center": ("technician", "The CBRE data-centre shift-technician role uses my earlier HVAC service experience, practical fault-finding and equipment-handling background. I would confirm the rotating 12-hour roster and trade requirements first.", ["HVAC", "Data centre", "Rotating roster", "Field service"]),
    "Shift Technician- Air Conditioning & Refrigeration, Data Center": ("technician", "My earlier HVAC service work and later data-centre infrastructure exposure make this a credible practical pathway. I would confirm the rotating 12-hour roster, site location and trade requirements before applying.", ["HVAC", "Data centre", "Shift roster", "Field service"]),
    "ICT Support Technician": ("technician", "This is one of the closest matches to my recent endpoint and service-desk work. The Moorabbin location also makes the role practical from St Kilda.", ["L1/L2 desktop support", "Windows hardware and software", "Network troubleshooting", "Close to St Kilda"]),
    "Infrastructure Delivery — Network Technician": ("technician", "My NBN field-technician background and enterprise infrastructure experience provide a strong base for network technician work in data-centre delivery.", ["Layer 1 infrastructure", "Network technician", "Data centre", "Physical infrastructure"]),
    "Data Center Operations Technician Trainee": ("technician", "The explicit trainee structure is attractive because it combines server and networking exposure with a defined path to build data-centre operations capability. The listing is older, so availability must be checked first.", ["Trainee pathway", "Server and networking", "Data centre", "Training"]),
    "Conveyor Belt Splicing Trainee / Belt Technician": ("technician", "My earlier field telecommunications and HVAC work demonstrates practical fault-finding, site work and the ability to work with physical infrastructure. I am interested in learning the belt-technician trade properly.", ["Trainee pathway", "Practical work", "Field service", "Fault-finding"]),
    "Instrument Technician": ("technician", "My hospital endpoint migration experience gives me direct familiarity with clinical environments, strict continuity requirements and disciplined technical troubleshooting. I would need to confirm the instrument-specific qualification requirements.", ["Healthcare environment", "Technical troubleshooting", "Clinical continuity", "Qualification check"]),
    "Air-Conditioning & Refrigeration Apprentice — Data Centre": ("technician", "My previous HVAC service work and later data-centre infrastructure exposure make this a credible trade-pathway application. The listing specifies Year 3–4 apprentices, which must be confirmed before applying.", ["HVAC", "Data centre", "Apprenticeship", "Year 3–4 requirement"]),
    "Electrical Apprentice — Data Centre Facilities": ("technician", "My infrastructure background includes data-centre environmental controls and physical infrastructure, but no electrical licence or current electrical apprenticeship stage is claimed. The Year 3–4 requirement must be screened first.", ["Data centre", "Facilities", "Apprenticeship", "Requirement check"]),
    "Apprentice Vehicle Technician — Richmond, January 2027 intake": ("technician", "This is a deliberate career-change application. My transferable base is systematic mechanical and electrical fault-finding from HVAC, plus field infrastructure discipline; no automotive qualification is claimed.", ["Apprenticeship", "Training", "Career change", "Richmond"]),
    "Apprentice Technician": ("technician", "This is a deliberate practical career-change application. My HVAC and telecommunications background provides hands-on fault-finding and site experience, while the apprenticeship provides the formal automotive pathway.", ["Apprenticeship", "Automotive training", "Hands-on", "Career change"]),
    "Mower Operator": ("outdoor", "The Port Melbourne depot and City of Port Phillip work area make this the strongest local outdoor option. My field-service background includes multi-site work, equipment handling, systematic troubleshooting and early-start service schedules.", ["City of Port Phillip", "Port Melbourne", "Outdoor work", "Field service"]),
    "Qualified Gardener": ("outdoor", "I am interested in the Port Phillip outdoor work, but I do not claim a Cert III in Horticulture or prior commercial gardening experience. My relevant transferable experience is field service, equipment handling, site work and systematic maintenance.", ["Port Phillip", "Outdoor work", "Qualification check", "Field service"]),
    "Ranger — Parks and Gardens": ("outdoor", "My field technician and HVAC experience supports practical outdoor equipment work, site assessment and fault-finding. I do not claim parks, conservation or ranger experience, so the position requirements need careful review.", ["Parks and gardens", "Outdoor", "Field work", "Requirement check"]),
    "Park Asset Specialist": ("outdoor", "My infrastructure asset, inventory and site-assessment background is relevant to a park-asset role, although I do not claim prior council parks experience. I would bring disciplined record-keeping, fault identification and stakeholder communication.", ["Council", "Asset management", "Parks", "Site assessment"]),
    "Brushcutting Team Member": ("outdoor", "My earlier field and HVAC roles provide a base for practical outdoor work, equipment handling and following repeatable maintenance procedures. I do not claim brushcutter or horticulture qualifications.", ["Outdoor", "Council contract", "Equipment handling", "Training needed"]),
    "Sports Team Member": ("outdoor", "The community-facilities focus fits my customer-facing service, asset-control and field-work background. I would need to confirm the balance of indoor administration, sports operations and outdoor duties.", ["Council", "Community facilities", "Asset control", "Customer service"]),
    "Maintenance / Groundskeeper": ("outdoor", "My field service, HVAC maintenance and site-assessment experience provides transferable grounds and facilities support skills. I do not claim horticultural qualifications, so the role’s exact requirements need verification.", ["Groundskeeping", "Facilities", "Southern suburbs", "Requirement check"]),
    "Panel Beater & Apprentice Spray Painter": ("local", "This is a local practical-work application with an advertised apprentice-to-leadership pathway. My transferable experience comes from HVAC and telecommunications fault-finding; no panel-beating qualification is claimed.", ["St Kilda", "Apprenticeship", "Workshop", "Career change"]),
    "Part-Time Customer Service and Sales Assistant": ("local", "The St Kilda location and small part-time commitment make this a practical local option. My experience includes customer-facing technical support, clear explanations, stock and asset control, and dependable service operations.", ["St Kilda", "Part-time", "Customer service", "Asset control"]),
    "Casual Housekeeper": ("local", "This is a local-work transition application. I do not claim housekeeping experience, but I bring disciplined procedures, attention to equipment and inventory, service schedules, documentation and reliable task ownership.", ["St Kilda", "Casual", "Local work", "Transferable skills"]),
    "Cook / Chef / Kitchen Staff": ("local", "This is a deliberate local career-change application. The master résumé does not claim commercial kitchen experience, so this pack focuses only on transferable reliability, service operations, learning ability and structured work.", ["St Kilda", "Part-time", "Career change", "Training needed"]),
    "Retail Planogram Merchandiser — Casual": ("local", "The role’s local, field-based and inventory-oriented structure connects with my asset-control, site-assessment, documentation and customer-facing support experience. The advertised car and licence requirement must be confirmed.", ["St Kilda", "Casual", "Inventory", "Car/licence check"]),
    "Barista / Bartender": ("local", "This is a deliberate local hospitality application. I do not claim barista, bartending or RSA experience; the application focuses on transferable customer service, calm problem-solving and willingness to learn the venue’s procedures.", ["St Kilda", "Part-time", "Hospitality", "RSA check"]),
    "Team Member": ("local", "The listing says no experience is needed and highlights training. My recent support roles demonstrate customer communication, reliable procedures, teamwork, queue management and the ability to learn systems quickly.", ["St Kilda", "Training", "Customer service", "Entry-level"]),
    "LEGO Robotics and Science Tutor / Instructor": ("local", "This is the strongest local non-infrastructure match because it combines technical communication, client workshops, automation projects and explaining complex concepts to non-technical audiences.", ["South Melbourne", "STEM", "Technical communication", "Part-time"]),
    "Medical Receptionist — Part-time": ("local", "My service-centre and healthcare project experience provides transferable customer communication, scheduling, documentation, privacy-conscious support and clinical-environment familiarity. I do not claim prior medical-reception experience.", ["St Kilda East", "Part-time", "Healthcare environment", "Experience check"]),
}

CONTACTS = {
    # No direct hiring contacts were published in the retrieved role records.
}

def slug(text):
    text = text.lower().replace("&", "and").replace("—", "-")
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text[:95]

def filename_prefix(role):
    base = slug(role['company'] + '_' + role['title'])
    duplicate_bases = Counter(slug(item['company'] + '_' + item['title']) for item in ALL_ROLE_RECORDS)
    suffix = f"_{slug(role.get('location', ''))}" if duplicate_bases[base] > 1 else ""
    return f"2026-08-08_{base}{suffix}"

def write_resume(prefix, title, category, reason, tags_list, audit):
    cfg = CATEGORY[category]
    exact_terms = audit.get("matched_terms", [])
    skills = " · ".join(dict.fromkeys(exact_terms + [item.strip() for item in cfg["skills"].split("·")]))
    lines = [
        "# Sam Ludwig",
        "Melbourne, VIC | 0405 993 245 | sam.ludwig@gmail.com",
        "samludwig.au | github.com/Ludwixix",
        "",
        f"## Target Role: {title}",
        "",
        "### Professional Summary",
        cfg["summary"],
        "",
        "### Profile",
        natural_reason(reason),
        "",
        "### Core Skills",
        skills,
        "",
        "### Professional Experience",
    ]
    for experience in sorted(EXPERIENCE_SECTIONS[category], key=experience_year, reverse=True):
        lines += [f"### {experience['heading']}", experience["period"]]
        lines += [f"- {bullet}" for bullet in experience["bullets"]]
        lines.append("")
    projects = PROJECTS_BY_CATEGORY.get(category, [])
    if projects:
        lines += ["### Selected Projects"]
        lines += [f"- {project}" for project in projects]
        lines.append("")
    lines += [
        "### Qualifications",
        "AZ-104 Azure Administrator Associate · AZ-900 Azure Fundamentals · ITIL 4 Foundation · Certified Scrum Master · Diploma of Information Technology — Coder Academy",
        "",
        "### Work Rights",
        "Australian citizen · unrestricted Australian work rights · available immediately",
    ]
    path = APP / f"{prefix}_resume.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path

def write_cover(prefix, role, category, reason, tags_list, audit):
    cfg = CATEGORY[category]
    title = role["title"]
    company = employer_name(role)
    location = role["location"]
    body = [
        "# Sam Ludwig",
        "Melbourne, VIC | 0405 993 245 | sam.ludwig@gmail.com",
        "",
        f"**Re: {title} — {company}**",
        "",
        "Dear Hiring Manager,",
        "",
        f"I’m applying for the {title} position with {company}. {natural_reason(reason)}",
        "",
        "My recent experience combines enterprise support with earlier field-based technical work. At Australia Post via Capgemini, I delivered hardware diagnostics, Windows imaging, endpoint provisioning, Autopilot/UEM enrolment, inventory control, loan-device management and compliant disposal. At St John of God Health Care, I led Windows 11 migration across more than 100 clinical endpoints using Autopilot and Intune, with application validation and hypercare in a live hospital environment.",
        "",
        "Earlier work at NBN Co and PolaAir developed practical site assessment, physical infrastructure installation, equipment handling, systematic fault-finding and customer communication across Melbourne locations. My Capgemini experience also adds strong documentation, process discipline, stakeholder communication, PowerShell automation and enterprise service operations.",
        "",
        f"What appeals to me about the role is the combination of {', '.join(audit.get('matched_terms', [])[:3] or tags_list[:3]).lower()}. I’d bring dependable task ownership, clear communication and a willingness to learn the way your team works.",
        "",
        "I’m happy to confirm any licence, qualification, check, vehicle, roster or prior-industry requirements before progressing.",
        "",
        "Thank you for considering my application. I would welcome a conversation about how my background could contribute to your team.",
        "",
        "Yours sincerely,",
        "Sam Ludwig",
    ]
    path = APP / f"{prefix}_cover_letter.md"
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return path

def write_email(prefix, role, category, reason, tags_list, audit):
    contact = CONTACTS.get(role["title"], {})
    email = contact.get("email")
    phone = contact.get("phone")
    manager = contact.get("manager")
    company = employer_name(role)
    body = [
        f"# Opening Email — {role['title']}",
        "",
        f"**Company:** {company}",
        f"**Location:** {role['location']}",
        f"**Application link:** {role['url']}",
        *([f"**Hiring manager:** {manager}"] if manager else []),
        *([f"**Direct email:** {email}"] if email else []),
        *([f"**Direct phone:** {phone}"] if phone else []),
        "",
        "## Subject",
        f"Application — {role['title']} — Sam Ludwig",
        "",
        "## Email body",
        f"Hello {manager or 'Hiring Manager'},",
        "",
        f"I’m writing about the {role['title']} position with {company}. {natural_reason(reason)}",
        "",
        "My background includes enterprise technical support, endpoint lifecycle management, field infrastructure, systematic fault-finding, customer communication and process-focused documentation.",
        "",
        f"The areas most relevant to the role are {', '.join(audit.get('matched_terms', [])[:3] or tags_list[:3]).lower()}.",
        "",
        "I’d welcome a brief conversation about the role and any position-specific requirements.",
        "",
        "Regards,",
        "Sam Ludwig",
        "0405 993 245",
        "sam.ludwig@gmail.com",
        "",
    ]
    path = APP / f"{prefix}_opening_email.md"
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return path

def attach_paths(role, prefix, resume_path, cover_path, email_path, audit_path):
    resume_pdf = resume_path.with_suffix(".pdf")
    cover_pdf = cover_path.with_suffix(".pdf")
    role["resume"] = resume_pdf.relative_to(ROOT).as_posix()
    role["cover"] = cover_pdf.relative_to(ROOT).as_posix()
    role["resume_md"] = resume_path.relative_to(ROOT).as_posix()
    role["cover_md"] = cover_path.relative_to(ROOT).as_posix()
    role["email_md"] = email_path.relative_to(ROOT).as_posix()
    role["audit_json"] = audit_path.relative_to(ROOT).as_posix()
    role["audit"] = json.loads(audit_path.read_text(encoding="utf-8"))
    role["contact_email"] = CONTACTS.get(role["title"], {}).get("email")
    role["contact_phone"] = CONTACTS.get(role["title"], {}).get("phone")
    role["hiring_manager"] = CONTACTS.get(role["title"], {}).get("manager")
    role["application_materials"] = "Tailored résumé, cover letter and opening email"
    role.setdefault("application_route", role.get("url"))
    if role.get("source") == "Indeed":
        role.setdefault("application_route_type", "Indeed listing")
    elif "careers" in str(role.get("url", "")).lower() or "livehire" in str(role.get("url", "")).lower():
        role.setdefault("application_route_type", "Direct employer or government route")
    else:
        role.setdefault("application_route_type", "Job-board or employer route")
    role.setdefault("listing_verification", "Individual listing captured from a non-LinkedIn source; confirm availability before applying.")

count_new = 0
count_emails = 0
for role in data["jobs"]:
    if role.get("company") == "LGT Wealth Management Australia":
        reason = "The LGT Infrastructure Engineer role is a strong match for my experience across Windows, Azure, Microsoft 365, Entra ID, PowerShell automation, incident response, documentation, and production support."
    elif role.get("company") == "Victorian Institute of Teaching":
        reason = "The Victorian Institute of Teaching Senior Cloud Engineer role matches my Azure, Microsoft 365, Entra ID, hybrid identity, automation, enterprise support, and public-sector delivery experience."
    elif role.get("company") == "Victorian Government":
        reason = "The Victorian Government Senior Cloud Engineer role matches my Azure, Microsoft 365, identity, automation, enterprise support, and public-sector delivery experience."
    else:
        reason = CORE_EMAILS.get(role["title"], role["why"])
    tags_list = ["Core infrastructure", "Tailored existing materials", "Verify listing"]
    existing_resume = role.get("resume", "")
    # Use the current employer name for the VIT listing. The previous bundle
    # stored this route under a generic Victorian Government filename.
    if role.get("company") == "Victorian Institute of Teaching":
        prefix = filename_prefix(role)
    else:
        prefix = Path(existing_resume).stem.removesuffix("_resume") if existing_resume else filename_prefix(role)
    audit = build_audit(role, "core", reason, tags_list)
    audit_path = AUDITS / f"{prefix}_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    resume_path = write_resume(prefix, role["title"], "core", reason, tags_list, audit)
    cover_path = write_cover(prefix, role, "core", reason, tags_list, audit)
    email_path = write_email(prefix, role, "core", reason, tags_list, audit)
    attach_paths(role, prefix, resume_path, cover_path, email_path, audit_path)
    count_emails += 1

for category, roles in data.get("sections", {}).items():
    for role in roles:
        override = ROLE_OVERRIDES.get(role["title"])
        if not override:
            raise RuntimeError(f"No tailoring profile exists for new role: {role['title']}")
        cat, reason, tags_list = override
        prefix = filename_prefix(role)
        audit = build_audit(role, cat, reason, tags_list)
        audit_path = AUDITS / f"{prefix}_audit.json"
        audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        resume_path = write_resume(prefix, role["title"], cat, reason, tags_list, audit)
        cover_path = write_cover(prefix, role, cat, reason, tags_list, audit)
        email_path = write_email(prefix, role, cat, reason, tags_list, audit)
        attach_paths(role, prefix, resume_path, cover_path, email_path, audit_path)
        count_new += 1
        count_emails += 1

# Store a compact, human-readable index for quick application handling.
data["updated"] = data.get("updated", "2026-08-10T12:23:00+10:00")
data["search_area"] = "Melbourne, St Kilda area, and remote Australia"
data["policy"] = "LinkedIn excluded. Individual listings and direct employer or government routes are preferred. Search-only sources are labelled and must be verified manually. No applications or emails are submitted automatically."
index = []
for role in data["jobs"]:
    index.append({"lane":"core", "company":role["company"], "title":role["title"], "location":role["location"], "source":role.get("source"), "application_route":role.get("application_route", role.get("url")), "application_route_type":role.get("application_route_type"), "listing_verification":role.get("listing_verification"), "application_url":role["url"], "resume":role.get("resume"), "cover":role.get("cover"), "resume_source":role.get("resume_md"), "cover_source":role.get("cover_md"), "opening_email":role.get("email_md"), "audit":role.get("audit_json"), "fit":role.get("audit", {}).get("fit"), "matched_terms":role.get("audit", {}).get("matched_terms", []), "gaps":role.get("audit", {}).get("unsupported_or_unverified_terms", []), "requirements_to_confirm":role.get("audit", {}).get("requirements_to_confirm", []), "contact_email":role.get("contact_email"), "contact_phone":role.get("contact_phone"), "hiring_manager":role.get("hiring_manager")})
for category, roles in data.get("sections", {}).items():
    for role in roles:
        index.append({"lane":category, "company":role["company"], "title":role["title"], "location":role["location"], "source":role.get("source"), "application_route":role.get("application_route", role.get("url")), "application_route_type":role.get("application_route_type"), "listing_verification":role.get("listing_verification"), "application_url":role["url"], "resume":role.get("resume"), "cover":role.get("cover"), "resume_source":role.get("resume_md"), "cover_source":role.get("cover_md"), "opening_email":role.get("email_md"), "audit":role.get("audit_json"), "fit":role.get("audit", {}).get("fit"), "matched_terms":role.get("audit", {}).get("matched_terms", []), "gaps":role.get("audit", {}).get("unsupported_or_unverified_terms", []), "requirements_to_confirm":role.get("audit", {}).get("requirements_to_confirm", []), "contact_email":role.get("contact_email"), "contact_phone":role.get("contact_phone"), "hiring_manager":role.get("hiring_manager")})
(ROOT / "application_pack_index.json").write_text(json.dumps({"generated":data["updated"], "applications_submitted":False, "roles":index}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
DATA_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Generated tailored CVs and cover letters for {count_new} new roles")
print(f"Generated opening emails for {count_emails} roles")
print(f"Wrote application_pack_index.json with {len(index)} roles")
