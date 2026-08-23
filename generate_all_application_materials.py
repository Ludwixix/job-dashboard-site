#!/usr/bin/env python3
"""
Enhanced Application Materials Generator

Generates multi-dimensional job scoring, dynamically tailored resumes,
and company-specific cover letters for Sam Ludwig's job applications.

All content is derived from the master resume and job_profile.json.
No experience or skills are fabricated.
"""

from pathlib import Path
import json
import re
from collections import Counter
from datetime import datetime
from typing import Optional

ROOT = Path(__file__).parent
APP = ROOT / "applications"
AUDITS = ROOT / "application_audits"
DATA_PATH = ROOT / "scrapers" / "jobs_combined.json"
MASTER = ROOT / "resume.md"
JOB_PROFILE = ROOT / "job_profile.json"

APP.mkdir(exist_ok=True)
AUDITS.mkdir(exist_ok=True)

master = MASTER.read_text(encoding="utf-8")
profile = json.loads(JOB_PROFILE.read_text(encoding="utf-8"))

# Verify master resume integrity
for required in ("Sam Ludwig", "0405 993 245", "sam.ludwig@gmail.com", "Australian Citizen"):
    if required not in master:
        raise RuntimeError(f"Master résumé is missing required verified source text: {required}")

data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

ALL_ROLE_RECORDS = list(data.get("jobs", []))
for _section_roles in data.get("sections", {}).values():
    ALL_ROLE_RECORDS.extend(_section_roles)

# ─────────────────────────────────────────────────────────────────────────
# Candidate skill knowledge base (from job_profile.json + master resume)
# Each skill has: name, aliases, proficiency (expert/advanced/proficient/basic),
# category, years_experience, related_achievements
# ─────────────────────────────────────────────────────────────────────────
SKILL_KB = {
    "Microsoft 365": {
        "aliases": ["microsoft 365", "m365", "modern workplace"],
        "proficiency": "expert",
        "category": "m365_cloud",
        "years": 6,
        "achievements": [
            "Managed enterprise Microsoft 365 environment supporting 660,000+ users across SharePoint, Exchange, Teams, and Entra ID",
            "Administered Exchange Hybrid, Teams, SharePoint Online, and Google Workspace in a government environment",
            "Built ServiceNow integration with M365 presence data for automated workload distribution",
        ],
    },
    "SharePoint": {
        "aliases": ["sharepoint", "spfx", "sharepoint online", "sharepoint server", "pnp"],
        "proficiency": "expert",
        "category": "m365_cloud",
        "years": 6,
        "achievements": [
            "Managed largest SharePoint farm in Southern Hemisphere: 660,000+ users, 1,000+ sites, 99.9% uptime",
            "Delivered enterprise SharePoint intranets for Victoria Police, Transurban, Cimic Group using SPFx/React/TypeScript",
            "Engineered PnP PowerShell to audit and enforce MFA compliance across 200+ SharePoint sites",
        ],
    },
    "Exchange": {
        "aliases": ["exchange", "exchange online", "exchange hybrid", "mail flow", "email"],
        "proficiency": "advanced",
        "category": "m365_cloud",
        "years": 5,
        "achievements": [
            "Administered Exchange Hybrid and Teams, resolving complex mail-flow, calendar, and federation issues",
            "Resolved mail-flow routing issues and cross-tenant collaboration scenarios",
        ],
    },
    "Teams": {
        "aliases": ["teams", "microsoft teams", "teams voice", "teams admin"],
        "proficiency": "advanced",
        "category": "m365_cloud",
        "years": 4,
        "achievements": [
            "Enterprise Teams rollout, governance, meeting policies, federation",
            "Resolved complex mail-flow, calendar, and federation issues across Exchange and Teams",
        ],
    },
    "Entra ID": {
        "aliases": ["entra", "entra id", "azure ad", "azure ad connect", "identity", "hybrid identity", "adfs"],
        "proficiency": "expert",
        "category": "identity_security",
        "years": 5,
        "achievements": [
            "Oversaw AD/Entra ID/Google Workspace sync, resolving identity conflicts for seamless SSO",
            "Managed hybrid identity across three identity providers (AD, Entra ID, Google Workspace)",
            "Configured Conditional Access, MFA enforcement, and SSPR",
        ],
    },
    "Azure": {
        "aliases": ["azure", "azure vm", "azure functions", "azure automation", "azure devops", "azure portal"],
        "proficiency": "advanced",
        "category": "m365_cloud",
        "years": 4,
        "achievements": [
            "Spearheaded Azure cloud adoption and legacy application remediation, aligned with ACSC Essential 8",
            "Implemented Azure DevOps CI/CD pipelines reducing deployment cycles by 25%",
            "Azure Administrator Associate (AZ-104) certified",
        ],
    },
    "Intune": {
        "aliases": ["intune", "endpoint", "euc", "mdm", "mam", "microsoft intune"],
        "proficiency": "advanced",
        "category": "endpoint_management",
        "years": 3,
        "achievements": [
            "Led Windows 11 enterprise migration across 100+ clinical endpoints using Autopilot and Intune",
            "Managed Intune policy application, compliance verification, and device configuration profiles",
            "Autopilot/UEM enrolment, SOE builds, and device lifecycle management",
        ],
    },
    "Windows": {
        "aliases": ["windows", "windows 10", "windows 11", "windows server", "desktop", "workstation", "soe"],
        "proficiency": "advanced",
        "category": "endpoint_management",
        "years": 6,
        "achievements": [
            "Led Windows 11 migration across 100+ clinical endpoints",
            "Managed Windows 10/11 migrations, standardised SOE builds, Autopilot/UEM enrolment",
            "Windows Server 2012R2–2022, Active Directory Domain Services, Group Policy Management",
        ],
    },
    "PowerShell": {
        "aliases": ["powershell", "pnp powershell", "automation", "scripting"],
        "proficiency": "expert",
        "category": "automation_devops",
        "years": 5,
        "achievements": [
            "Engineered PnP PowerShell to audit and enforce MFA compliance across 200+ SharePoint sites",
            "Built PowerShell automation reducing migration processing by 87% (2 hours to 15 minutes)",
            "PowerShell 5.1/7, PnP PowerShell, Exchange Online Management, Graph API",
        ],
    },
    "Python": {
        "aliases": ["python", "python3"],
        "proficiency": "advanced",
        "category": "automation_devops",
        "years": 3,
        "achievements": [
            "Built M365 diagnostic GUI tool for L1 staff PowerShell diagnostics",
            "Developed Python and PowerShell patching scripts reducing manual effort by 20%",
            "Selenium, web scraping, API integration",
        ],
    },
    "ServiceNow": {
        "aliases": ["servicenow", "service desk", "service-desk", "itsm"],
        "proficiency": "advanced",
        "category": "service_management",
        "years": 4,
        "achievements": [
            "Built ServiceNow workload distribution engine integrating M365 presence data with ticket queues",
            "Built ServiceNow automation that removed hundreds of hours of repetitive data entry per month",
            "ServiceNow integration with M365 presence data and algorithmic workload engine",
        ],
    },
    "Active Directory": {
        "aliases": ["active directory", "ad ds", "ad domain services", "group policy"],
        "proficiency": "advanced",
        "category": "identity_security",
        "years": 5,
        "achievements": [
            "Managed AD/Entra ID/Google Workspace sync, resolving identity conflicts for seamless SSO",
            "Active Directory Domain Services, Group Policy Management, DNS, DHCP",
        ],
    },
    "ITIL": {
        "aliases": ["itil", "itil 4", "incident management", "problem management", "change management"],
        "proficiency": "advanced",
        "category": "service_management",
        "years": 4,
        "achievements": [
            "ITIL 4 certified — incident, problem, change, service request, SLA management",
            "Consistently >90% SLA resolution across 40+ concurrent tickets",
        ],
    },
    "Autopilot": {
        "aliases": ["autopilot", "windows autopilot"],
        "proficiency": "advanced",
        "category": "endpoint_management",
        "years": 3,
        "achievements": [
            "100% Autopilot adherence in clinical Windows 11 migration",
            "Hardware hash registration, profile assignment, white-glove deployment",
        ],
    },
    "CI/CD": {
        "aliases": ["ci/cd", "cicd", "azure devops", "devops", "pipelines"],
        "proficiency": "advanced",
        "category": "automation_devops",
        "years": 4,
        "achievements": [
            "Implemented full CI/CD pipelines using Azure DevOps and Git, reducing deployment cycles by 25%",
            "Automated builds, testing, quality gates, and streamlined release management",
        ],
    },
    "React": {
        "aliases": ["react", "reactjs", "react.js"],
        "proficiency": "advanced",
        "category": "automation_devops",
        "years": 3,
        "achievements": [
            "Delivered 5+ enterprise SharePoint intranets using SPFx/React/TypeScript",
        ],
    },
    "TypeScript": {
        "aliases": ["typescript"],
        "proficiency": "advanced",
        "category": "automation_devops",
        "years": 3,
        "achievements": [
            "Delivered enterprise SharePoint solutions with React and TypeScript",
        ],
    },
    "Git": {
        "aliases": ["git", "github", "version control"],
        "proficiency": "advanced",
        "category": "automation_devops",
        "years": 5,
        "achievements": [
            "Advanced branching, merging, rebasing across Azure DevOps and GitHub",
            "Implemented CI/CD pipelines with Git-triggered automated builds",
        ],
    },
    "Network": {
        "aliases": ["network", "networking", "layer 1", "layer 1 networking", "fibre", "copper", "cabling", "structured cabling", "fault-finding"],
        "proficiency": "proficient",
        "category": "infrastructure",
        "years": 2,
        "achievements": [
            "Layer 1 infrastructure deployments, physical cabling, fault-finding at NBN Co",
            "Fibre optic and copper structured cabling across residential and commercial environments",
        ],
    },
    "Security": {
        "aliases": ["security", "cybersecurity", "cyber", "essential 8", "acsc", "conditional access", "mfa", "defender", "purview", "dlp"],
        "proficiency": "advanced",
        "category": "identity_security",
        "years": 4,
        "achievements": [
            "Aligned hybrid-cloud infrastructure with ACSC Essential 8 maturity model",
            "MFA enforcement strategy, Conditional Access policy design, risk-based policies",
            "Microsoft Purview (DLP, retention policies, eDiscovery, litigation hold)",
        ],
    },
    "Data Centre": {
        "aliases": ["data centre", "data center", "server", "rack", "facilities", "physical infrastructure"],
        "proficiency": "proficient",
        "category": "infrastructure",
        "years": 1,
        "achievements": [
            "Data centre environmental controls, HVAC/thermal management, power distribution, rack-and-stack",
            "Hardware provisioning and physical infrastructure fundamentals",
        ],
    },
    "HVAC": {
        "aliases": ["hvac", "air conditioning", "refrigeration", "thermal", "environmental controls"],
        "proficiency": "proficient",
        "category": "infrastructure",
        "years": 1,
        "achievements": [
            "Installed, maintained, and repaired commercial HVAC systems",
            "Systematic mechanical and electrical fault-finding under time pressure",
        ],
    },
    "Documentation": {
        "aliases": ["documentation", "rca", "root cause analysis", "runbook", "knowledge base", "as-built"],
        "proficiency": "expert",
        "category": "service_management",
        "years": 5,
        "achievements": [
            "Produced comprehensive as-built documentation, RCA reports, and operational runbooks",
            "Created searchable knowledge base reducing resolution time for recurring incidents",
            "RCA reports reduced repeat incidents by 15% over 12 months",
        ],
    },
    "Customer Support": {
        "aliases": ["customer support", "customer service", "user support", "service", "help desk"],
        "proficiency": "advanced",
        "category": "service_management",
        "years": 6,
        "achievements": [
            "Delivered comprehensive L1/L2 face-to-face and remote technical support",
            "Client-facing technical workshops driving 20% increase in M365 adoption",
            "Resolved complex issues for clinical, government, and retail environments",
        ],
    },
    "SharePoint Development": {
        "aliases": ["sharepoint development", "spfx development", "web parts", "sharepoint framework"],
        "proficiency": "expert",
        "category": "automation_devops",
        "years": 3,
        "achievements": [
            "Delivered 5+ enterprise SharePoint intranets using SPFx/React/TypeScript",
            "React SPFx web parts, extension development",
        ],
    },
    "Endpoint Lifecycle": {
        "aliases": ["endpoint lifecycle", "device lifecycle", "provisioning", "imaging", "disposal"],
        "proficiency": "advanced",
        "category": "endpoint_management",
        "years": 4,
        "achievements": [
            "Managed complete endpoint lifecycle from procurement to disposal",
            "OS migrations, device imaging, Autopilot/UEM enrolment, compliant disposal",
        ],
    },
    "Compliance": {
        "aliases": ["compliance", "governance", "iso 27001", "nist", "policy", "audit"],
        "proficiency": "advanced",
        "category": "identity_security",
        "years": 4,
        "achievements": [
            "ISO 27001 governance frameworks at Engage Squared",
            "ACSC Essential 8 maturity model alignment",
            "MFA compliance auditing across 200+ sensitive SharePoint sites",
        ],
    },
    "Agile": {
        "aliases": ["agile", "scrum", "kanban", "sprint", "backlog"],
        "proficiency": "advanced",
        "category": "service_management",
        "years": 3,
        "achievements": [
            "Certified Scrum Master (CSM)",
            "Sprint planning, backlog refinement, daily stand-ups, retrospective facilitation",
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────
# Experience entries (canonical source of truth)
# ─────────────────────────────────────────────────────────────────────────
EXPERIENCE_ENTRIES = [
    {
        "id": "australia_post",
        "heading": "L2/L3 Technical Support Engineer — Australia Post via Capgemini",
        "period": "February 2026–June 2026",
        "location": "Melbourne, Victoria",
        "years_from": 2026, "years_to": 2026,
        "skills_used": ["Windows", "Endpoint Lifecycle", "ServiceNow", "Customer Support", "Autopilot", "Intune", "Security"],
        "relevance_weights": {
            "core": 0.9,
            "technician": 0.85,
            "outdoor": 0.4,
            "local": 0.7,
        },
        "bullets_by_category": {
            "core": [
                "Delivered L1/L2 endpoint support covering hardware diagnostics, Windows imaging, break-fix work, provisioning, loan devices, accessories, and user access.",
                "Managed Windows 10/11 migrations, standardised SOE builds, Autopilot/UEM enrolment, inventory, and compliant equipment disposal.",
                "Built ServiceNow automation that removed hundreds of hours of repetitive manual data entry each month while working within locked-down endpoint controls.",
                "Supported complex infrastructure faults as an escalation point for L3 engineering teams and documented fixes for repeatable service operations.",
            ],
            "technician": [
                "Diagnosed and repaired Windows endpoint hardware, performed imaging and recovery, provisioned devices, managed loan equipment, and supported users through a high-volume service centre.",
                "Handled Autopilot/UEM enrolment, Windows 10/11 migrations, SOE builds, inventory, accessories, and compliant disposal across the endpoint lifecycle.",
                "Built ServiceNow automation that removed hundreds of hours of repetitive data entry each month.",
            ],
            "outdoor": [
                "Managed equipment, inventory, loan devices, accessories, provisioning, repair, and compliant disposal in a high-volume service operation.",
                "Worked through complex faults, followed documented procedures, and coordinated escalations with engineering teams.",
            ],
            "local": [
                "Supported users with hardware, Windows, provisioning, repairs, access, inventory, and service requests in a busy customer-facing environment.",
                "Managed loan devices, accessories, endpoint records, and compliant disposal while keeping work moving against service targets.",
            ],
        },
    },
    {
        "id": "st_john",
        "heading": "Endpoint Migration Engineer — St John of God Health Care",
        "period": "October 2025–January 2026",
        "location": "Melbourne, Victoria",
        "years_from": 2025, "years_to": 2026,
        "skills_used": ["Windows", "Intune", "Autopilot", "Customer Support", "Documentation", "Security"],
        "relevance_weights": {
            "core": 0.85,
            "technician": 0.8,
            "outdoor": 0.35,
            "local": 0.65,
        },
        "bullets_by_category": {
            "core": [
                "Led a Windows 11 migration across more than 100 clinical endpoints using Autopilot, Intune, SOE controls, application validation, and post-deployment hypercare.",
                "Managed hardware preparation, Autopilot enrolment, profile assignment, Intune policy application, compliance checks, user handover, and training.",
                "Worked directly with clinical staff and engineering teams to resolve compatibility issues affecting EMR, diagnostic imaging, and administration systems.",
            ],
            "technician": [
                "Migrated more than 100 clinical endpoints to Windows 11 using Autopilot and Intune while supporting live hospital operations.",
                "Prepared hardware, applied policies, checked compliance, validated clinical applications, handed devices to users, and provided hypercare.",
                "Explained technical issues clearly to clinical staff and worked with engineering teams to resolve compatibility problems.",
            ],
            "outdoor": [
                "Prepared and deployed more than 100 endpoints in live clinical environments, with structured checks, handover, and hypercare.",
                "Worked with staff and technical teams to resolve equipment and application issues without disrupting clinical operations.",
            ],
            "local": [
                "Prepared, deployed, and supported more than 100 Windows 11 endpoints in a live hospital environment.",
                "Explained technical issues to staff, coordinated fixes, validated applications, and supported users after handover.",
            ],
        },
    },
    {
        "id": "capgemini_edu",
        "heading": "Senior Managed Services Engineer — Capgemini, consultant to Department of Education Victoria",
        "period": "December 2021–2023",
        "location": "Melbourne, Victoria",
        "years_from": 2021, "years_to": 2023,
        "skills_used": ["SharePoint", "Exchange", "Teams", "Entra ID", "Azure", "PowerShell", "Active Directory", "Security", "Documentation", "CI/CD", "Agile", "Compliance", "Customer Support"],
        "relevance_weights": {
            "core": 1.0,
            "technician": 0.6,
            "outdoor": 0.25,
            "local": 0.45,
        },
        "bullets_by_category": {
            "core": [
                "Managed SharePoint Online, Exchange Online, Teams, Entra ID, hybrid identity, Azure, and Google Workspace in a government environment supporting 660,000+ users across 1,000+ site collections.",
                "Acted as a Tier-3 escalation point, led root-cause analysis, and introduced preventive fixes that reduced repeat incidents by 15 percent over 12 months.",
                "Built PnP PowerShell automation to audit and enforce MFA compliance across more than 200 sensitive SharePoint sites, replacing a month-long manual audit cycle.",
                "Supported Azure adoption, legacy remediation, Essential 8-aligned security baselines, mail-flow troubleshooting, identity synchronisation, and operational runbooks.",
            ],
            "technician": [
                "Supported enterprise infrastructure, endpoint, identity, Microsoft 365, Azure, ServiceNow, documentation, and escalation operations.",
                "Automated repetitive service work with PowerShell and investigated faults through structured root-cause analysis.",
            ],
            "outdoor": [
                "Maintained disciplined asset, incident, documentation, and escalation practices across enterprise infrastructure services.",
                "Used automation and root-cause analysis to reduce repeat work and improve service operations.",
            ],
            "local": [
                "Handled service requests, documentation, stakeholder communication, technical troubleshooting, and process improvement across enterprise systems.",
                "Built automation and knowledge resources that reduced repetitive work and helped teams resolve issues consistently.",
            ],
        },
    },
    {
        "id": "knosys",
        "heading": "Application Support Engineer — Knosys",
        "period": "December 2020–December 2021",
        "location": "Melbourne, Victoria",
        "years_from": 2020, "years_to": 2021,
        "skills_used": ["PowerShell", "Python", "Documentation", "Customer Support"],
        "relevance_weights": {
            "core": 0.7,
            "technician": 0.5,
            "outdoor": 0.15,
            "local": 0.35,
        },
        "bullets_by_category": {
            "core": [
                "Provided L3 support for the GreenOrbit enterprise intranet platform and resolved complex SQL, API, authentication, browser, and Windows Server issues within SLA.",
                "Built PowerShell automation that reduced migration processing time by 87 percent, from two hours to 15 minutes per batch, saving more than 10 hours of manual work each month.",
                "Developed Python and PowerShell patching scripts that reduced manual patching effort by 20 percent and improved cycle consistency.",
            ],
            "technician": [
                "Delivered L3 support across multiple enterprise clients including retail, healthcare, and government.",
                "Automated migration processing with PowerShell, reducing manual effort by 87 percent.",
                "Built Python and PowerShell patching scripts that improved cycle consistency.",
            ],
            "outdoor": [
                "Resolved complex platform issues through structured diagnostics and documentation.",
            ],
            "local": [
                "Provided technical support across multiple enterprise clients.",
                "Automated repetitive processes and documented solutions.",
            ],
        },
    },
    {
        "id": "engage_squared",
        "heading": "SharePoint Developer — Engage Squared",
        "period": "March 2018–December 2020",
        "location": "Melbourne, Victoria",
        "years_from": 2018, "years_to": 2020,
        "skills_used": ["SharePoint", "React", "TypeScript", "CI/CD", "Git", "SharePoint Development", "Compliance", "Agile"],
        "relevance_weights": {
            "core": 0.75,
            "technician": 0.35,
            "outdoor": 0.1,
            "local": 0.3,
        },
        "bullets_by_category": {
            "core": [
                "Delivered enterprise SharePoint Online intranets for Victoria Police, Transurban, and Cimic Group using SPFx, React, TypeScript, and PnP PowerShell.",
                "Implemented Azure DevOps and Git CI/CD pipelines that reduced deployment cycle times by 25 percent.",
                "Led legacy SharePoint migrations, governance work, client workshops, and post-launch L2/L3 support.",
            ],
            "technician": [
                "Delivered SharePoint solutions using SPFx, React, and TypeScript for enterprise clients.",
                "Implemented CI/CD pipelines and supported legacy migrations.",
            ],
            "outdoor": [
                "Delivered enterprise solutions through structured project delivery.",
            ],
            "local": [
                "Delivered custom enterprise solutions and provided post-launch support.",
            ],
        },
    },
    {
        "id": "nbn",
        "heading": "Telecommunications Technician — NBN Co",
        "period": "October 2016–November 2017",
        "location": "Melbourne, Victoria",
        "years_from": 2016, "years_to": 2017,
        "skills_used": ["Network", "HVAC", "Customer Support"],
        "relevance_weights": {
            "core": 0.3,
            "technician": 0.7,
            "outdoor": 0.6,
            "local": 0.5,
        },
        "bullets_by_category": {
            "core": [
                "Installed and maintained fibre and copper Layer 1 infrastructure across residential, commercial, and multi-dwelling sites.",
                "Performed physical fault-finding, connectivity diagnostics, NTD and router installation, CPE work, and site assessments.",
            ],
            "technician": [
                "Installed and maintained fibre and copper Layer 1 infrastructure across residential, commercial, and multi-dwelling sites.",
                "Performed physical fault-finding, connectivity diagnostics, NTD and router installation, CPE work, and site assessments.",
                "Worked to structured cabling standards while managing customer communication and multiple Melbourne locations.",
            ],
            "outdoor": [
                "Worked across Melbourne sites installing fibre and copper infrastructure, equipment, NTDs, routers, and customer-premises equipment.",
                "Completed site assessments, cable routing, physical fault-finding, equipment handling, and customer communication.",
            ],
            "local": [
                "Worked across Melbourne sites installing equipment and physical network infrastructure, assessing work areas, and resolving faults.",
                "Managed customer communication, equipment, structured procedures, and practical work in different environments.",
            ],
        },
    },
    {
        "id": "polaair",
        "heading": "HVAC Service Technician — PolaAir",
        "period": "2017",
        "location": "Melbourne, Victoria",
        "years_from": 2017, "years_to": 2017,
        "skills_used": ["HVAC", "Data Centre"],
        "relevance_weights": {
            "core": 0.15,
            "technician": 0.6,
            "outdoor": 0.55,
            "local": 0.4,
        },
        "bullets_by_category": {
            "core": [
                "Installed, maintained, and repaired commercial HVAC systems across Melbourne sites.",
                "Used systematic mechanical and electrical fault-finding under time pressure.",
            ],
            "technician": [
                "Installed, maintained, and repaired commercial HVAC systems across Melbourne sites.",
                "Used systematic mechanical and electrical fault-finding under time pressure and managed service schedules across multiple customers.",
                "Built practical experience with environmental controls, equipment handling, site work, and customer-facing service.",
            ],
            "outdoor": [
                "Installed, maintained, and repaired commercial HVAC systems across multiple sites.",
                "Managed service schedules, equipment, systematic fault-finding, and customer communication in field conditions.",
            ],
            "local": [
                "Completed scheduled maintenance, repair, equipment handling, and systematic fault-finding across commercial sites.",
                "Managed multiple service jobs and communicated directly with customers about the work required.",
            ],
        },
    },
]

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


# ═══════════════════════════════════════════════════════════════════════════
#  1. ENHANCED SCORING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

def _extract_requirements_from_job(role: dict) -> dict:
    """Parse job listing to extract skill requirements, seniority, and metadata."""
    title = (role.get("title") or "").lower()
    desc = (role.get("description") or "").lower()
    why = (role.get("why") or "").lower()
    tags = [t.lower() for t in role.get("tags", [])]
    company = (role.get("company") or "").lower()
    combined = f"{title} {desc} {why} {' '.join(tags)} {company}"

    # Extract seniority level from title
    seniority = "mid"
    if any(w in title for w in ("senior", "sr.", "lead", "principal", "staff", "architect")):
        seniority = "senior"
    elif any(w in title for w in ("junior", "jr.", "entry", "graduate", "assistant")):
        seniority = "junior"
    elif any(w in title for w in ("intern", "trainee", "apprentice")):
        seniority = "trainee"

    # Extract required years of experience from description
    years_required = None
    years_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)", desc)
    if years_match:
        years_required = int(years_match.group(1))
    elif seniority == "senior":
        years_required = 5
    elif seniority == "mid":
        years_required = 3
    elif seniority == "junior":
        years_required = 1
    else:
        years_required = 0

    # Check for remote/hybrid
    remote = role.get("remote", False)
    location = (role.get("location") or "").lower()
    if "remote" in combined:
        remote = True
    work_mode = "remote" if remote and "hybrid" not in combined else "hybrid" if "hybrid" in combined else "onsite"

    # Extract company size hints
    company = (role.get("company") or "").lower()
    company_size = "unknown"
    gov_keywords = ["government", "department of", "victorian", "council", "city of", "nbn", "department"]
    enterprise_keywords = ["bank", "insurance", "health", "hospital", "university", "large", "group"]
    startup_keywords = ["startup", "start-up", "scaleup", "scale-up"]
    msp_keywords = ["msp", "managed service", "consulting", "consultancy"]

    if any(k in company for k in gov_keywords):
        company_size = "government"
    elif any(k in company for k in enterprise_keywords):
        company_size = "enterprise"
    elif any(k in company for k in msp_keywords):
        company_size = "msp"
    elif any(k in company for k in startup_keywords):
        company_size = "startup"

    return {
        "seniority": seniority,
        "years_required": years_required,
        "remote": remote,
        "work_mode": work_mode,
        "company_size": company_size,
        "combined_text": combined,
    }


def _match_skills(role: dict, job_req: dict) -> dict:
    """Match candidate skills against job requirements. Returns matched, missing, with severity."""
    combined = job_req["combined_text"]
    matched = []
    missing = []
    all_job_skills_mentioned = []

    for skill_name, skill_info in SKILL_KB.items():
        # Check if this skill is mentioned in the job listing
        skill_mentioned = any(alias in combined for alias in skill_info["aliases"])
        if not skill_mentioned:
            continue

        all_job_skills_mentioned.append(skill_name)

        # Check if candidate has this skill
        candidate_has = any(alias in master.lower() for alias in skill_info["aliases"])
        if candidate_has:
            matched.append({
                "skill": skill_name,
                "proficiency": skill_info["proficiency"],
                "years": skill_info["years"],
                "top_achievement": skill_info["achievements"][0] if skill_info["achievements"] else "",
            })
        else:
            # Determine severity
            severity = "nice-to-have"
            if skill_info["proficiency"] in ("expert", "advanced"):
                severity = "preferred"
            if skill_name in ("SharePoint", "Azure", "Entra ID", "PowerShell", "Windows"):
                severity = "critical"
            missing.append({
                "skill": skill_name,
                "severity": severity,
                "proficiency_needed": skill_info["proficiency"],
            })

    return {
        "matched": matched,
        "missing": missing,
        "total_required": len(all_job_skills_mentioned),
    }


def score_job(role: dict, category: str = "core") -> dict:
    """
    Multi-dimensional job scoring.

    Score = Skill Match (40%) + Experience Alignment (25%) + Location/Remote Fit (15%)
          + Growth Potential (10%) + Company Size Fit (10%)

    Returns a dict with:
        score: 0-100 overall fit score
        dimensions: breakdown per dimension
        matched_skills: list of matched skills
        missing_skills: list of missing skills with severity
        strengths: top 3 reasons this is a good fit
        risks: top 3 concerns or gaps
        confidence: 0-1 confidence in this assessment
        fit_label: "Strong fit" / "Good fit" / "Partial fit" / "Weak fit"
    """
    job_req = _extract_requirements_from_job(role)
    skill_match = _match_skills(role, job_req)

    # ── Dimension 1: Skill Match (40%) ──
    if skill_match["total_required"] > 0:
        # Score based on match ratio and proficiency depth
        match_ratio = len(skill_match["matched"]) / skill_match["total_required"]
        # Bonus for expert-level matches
        expert_matches = sum(1 for s in skill_match["matched"] if s["proficiency"] == "expert")
        proficiency_bonus = min(0.15, expert_matches * 0.05)
        skill_score = min(100, (match_ratio * 85 + proficiency_bonus * 100))
    else:
        # No extractable skills — use tag-based heuristic
        skill_score = 50  # neutral default

    # ── Dimension 2: Experience Alignment (25%) ──
    candidate_years = 6  # 2018-present (SharePoint Developer through current)
    years_required = job_req["years_required"]
    if years_required > 0:
        if candidate_years >= years_required:
            exp_score = min(100, 70 + (candidate_years - years_required) * 5)
        else:
            shortfall = years_required - candidate_years
            exp_score = max(0, 70 - shortfall * 15)
    else:
        exp_score = 75  # No specific requirement — moderate score

    # Seniority match bonus/penalty
    seniority_map = {"junior": 0, "mid": 1, "senior": 2, "trainee": -1}
    candidate_level = 1  # Mid-level
    job_level = seniority_map.get(job_req["seniority"], 1)
    seniority_diff = candidate_level - job_level
    if seniority_diff == 0:
        exp_score = min(100, exp_score + 10)  # Perfect match
    elif seniority_diff == 1:
        exp_score = min(100, exp_score + 5)   # Slightly overqualified
    elif seniority_diff == -1:
        exp_score = max(0, exp_score - 10)    # Slightly underqualified
    elif seniority_diff <= -2:
        exp_score = max(0, exp_score - 25)    # Significantly underqualified

    # ── Dimension 3: Location/Remote Fit (15%) ──
    location = (role.get("location") or "").lower()
    melbourne_keywords = ["melbourne", "vic", "victoria", "cbd", "inner", "st kilda", "balaclava", "prahran"]

    if job_req["work_mode"] == "remote":
        loc_score = 95
    elif job_req["work_mode"] == "hybrid":
        loc_score = 85
    elif any(k in location for k in melbourne_keywords):
        loc_score = 80
    elif "australia" in location:
        loc_score = 60
    else:
        loc_score = 40

    # St Kilda area bonus
    st_kilda_area = ["st kilda", "balaclava", "prahran", "st kilda east", "melbourne 3004", "melbourne 3006"]
    if any(k in location for k in st_kilda_area):
        loc_score = min(100, loc_score + 15)

    # ── Dimension 4: Growth Potential (10%) ──
    growth_score = 50  # baseline
    combined = job_req["combined_text"]

    # Traineeships and certifications = high growth
    if any(w in combined for w in ["trainee", "traineeship", "apprentice", "apprenticeship",
                                     "certification", "learning", "development program",
                                     "career pathway", "mentored"]):
        growth_score = 90

    # Roles developing new skills
    new_skill_keywords = ["cybersecurity", "devops", "sre", "cloud native", "kubernetes",
                          "terraform", "aws", "gcp", "machine learning", "ai"]
    if any(k in combined for k in new_skill_keywords):
        growth_score = min(100, growth_score + 20)

    # Government roles with structured progression
    if job_req["company_size"] == "government":
        growth_score = min(100, growth_score + 10)

    # Consulting roles develop breadth
    if "consult" in combined:
        growth_score = min(100, growth_score + 10)

    # ── Dimension 5: Company Size Fit (10%) ──
    size_score = 50
    preference = "enterprise"  # Sam's natural fit

    if job_req["company_size"] == "government":
        size_score = 80  # Strong match — previous government experience
    elif job_req["company_size"] == "enterprise":
        size_score = 85
    elif job_req["company_size"] == "msp":
        size_score = 75  # Good match — Capgemini background
    elif job_req["company_size"] == "startup":
        size_score = 55  # Less typical but acceptable

    # ── Weighted total ──
    total = (
        skill_score * 0.40 +
        exp_score * 0.25 +
        loc_score * 0.15 +
        growth_score * 0.10 +
        size_score * 0.10
    )
    total = round(min(100, max(0, total)), 1)

    # ── Generate strengths ──
    strengths = []
    if skill_match["matched"]:
        top_skills = sorted(skill_match["matched"], key=lambda s: {"expert": 3, "advanced": 2, "proficient": 1}.get(s["proficiency"], 0), reverse=True)[:3]
        for s in top_skills:
            strengths.append(f"Strong {s['proficiency']} proficiency in {s['skill']}")
    if exp_score >= 80:
        strengths.append(f"Experience level aligns well ({candidate_years} years vs {years_required} required)")
    if loc_score >= 80:
        strengths.append(f"Location arrangement is practical ({job_req['work_mode']})")
    if job_req["company_size"] == "government" and any("education" in (role.get("company") or "").lower() for _ in [1]):
        strengths.append("Previous government environment experience (Dept. of Education Victoria)")
    if not strengths:
        strengths.append("Transferable skills from recent enterprise support roles")

    # ── Generate risks ──
    risks = []
    critical_missing = [s for s in skill_match["missing"] if s["severity"] == "critical"]
    if critical_missing:
        risks.append(f"Missing critical skill(s): {', '.join(s['skill'] for s in critical_missing[:3])}")
    if exp_score < 50:
        risks.append(f"Experience level may be below requirements ({candidate_years} years vs {years_required} required)")
    if job_req["seniority"] == "senior" and candidate_level < 2:
        risks.append("Role targets senior level; candidate is mid-level")
    if not job_req["remote"] and loc_score < 60:
        risks.append("Location may require significant commute")
    if len(risks) < 3 and skill_match["missing"]:
        preferred_missing = [s for s in skill_match["missing"] if s["severity"] == "preferred"][:3]
        if preferred_missing:
            risks.append(f"Preferred skills not demonstrated: {', '.join(s['skill'] for s in preferred_missing)}")
    if len(risks) < 3:
        risks.append("Confirm listing availability and exact requirements before applying")

    # ── Confidence ──
    confidence = 0.7  # baseline
    if role.get("description"):
        confidence += 0.1  # have full description
    if skill_match["total_required"] >= 3:
        confidence += 0.1  # enough skill signals
    if role.get("score", 0) > 0:
        confidence += 0.05  # manual score existed
    confidence = min(1.0, confidence)

    # ── Fit label ──
    if total >= 85:
        fit_label = "Strong fit"
    elif total >= 70:
        fit_label = "Good fit"
    elif total >= 50:
        fit_label = "Partial fit"
    else:
        fit_label = "Weak fit"

    return {
        "score": total,
        "fit_label": fit_label,
        "dimensions": {
            "skill_match": {"score": round(skill_score, 1), "weight": "40%", "matched": len(skill_match["matched"]), "total": skill_match["total_required"]},
            "experience_alignment": {"score": round(exp_score, 1), "weight": "25%", "candidate_years": candidate_years, "required_years": years_required, "seniority": job_req["seniority"]},
            "location_remote_fit": {"score": round(loc_score, 1), "weight": "15%", "work_mode": job_req["work_mode"]},
            "growth_potential": {"score": round(growth_score, 1), "weight": "10%"},
            "company_size_fit": {"score": round(size_score, 1), "weight": "10%", "company_size": job_req["company_size"]},
        },
        "matched_skills": skill_match["matched"],
        "missing_skills": skill_match["missing"],
        "strengths": strengths[:3],
        "risks": risks[:3],
        "confidence": round(confidence, 2),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  2. DYNAMIC RESUME GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

CATEGORY_CONFIGS = {
    "core": {
        "summary": "Infrastructure and Microsoft 365 engineer with progressive experience across Azure, Entra ID, Intune, Autopilot, Windows, SharePoint, Exchange, PowerShell, ServiceNow and enterprise service operations. Combines hands-on endpoint delivery with Tier-3 escalation, automation, security-aware change and durable documentation.",
        "skills_order": ["Microsoft 365", "SharePoint", "Azure", "Entra ID", "Intune", "PowerShell", "Exchange", "Teams", "Windows", "Autopilot", "ServiceNow", "Active Directory", "Security", "CI/CD", "Git", "Documentation"],
    },
    "technician": {
        "summary": "Hands-on technician and infrastructure professional combining recent enterprise endpoint support with earlier field telecommunications and HVAC service experience. Interested in structured training, practical troubleshooting and roles where technical capability develops through supervised work.",
        "skills_order": ["Windows", "Endpoint Lifecycle", "Intune", "Autopilot", "ServiceNow", "Network", "HVAC", "Customer Support", "Documentation", "PowerShell"],
    },
    "outdoor": {
        "summary": "Field-based infrastructure professional seeking practical outdoor, parks, facilities or council-contracted work. Brings site assessment, physical equipment handling, systematic fault-finding, customer communication, inventory discipline and experience working across Melbourne locations.",
        "skills_order": ["Network", "HVAC", "Data Centre", "Customer Support", "Documentation"],
    },
    "local": {
        "summary": "Melbourne-based professional seeking a practical local role in St Kilda and nearby suburbs. Brings dependable service-desk operations, customer communication, inventory control, field work, technical problem-solving, documentation and the ability to learn new procedures quickly.",
        "skills_order": ["Customer Support", "Documentation", "Endpoint Lifecycle", "Network", "HVAC"],
    },
}

# Category-specific profile reasons (replaces the old ROLE_OVERRIDES for resume summaries)
CATEGORY_PROFILE_REASONS = {
    "core": "The role aligns with my enterprise infrastructure, Microsoft 365, Azure, automation and service-operations background.",
    "technician": "The role connects my recent enterprise endpoint support with earlier field-based technical experience.",
    "outdoor": "My field technician and HVAC background provides transferable practical work skills.",
    "local": "My service-desk and technical support experience provides a strong local-work foundation.",
}


def _reorder_skills_for_job(category: str, job_skills: list[str], audit_matched: list[str]) -> list[str]:
    """Reorder skills so job-matched skills come first, then category defaults."""
    cfg = CATEGORY_CONFIGS[category]
    default_order = cfg["skills_order"]

    # Build priority list from job matches
    priority = []
    for s in job_skills:
        if s in SKILL_KB and s not in priority:
            priority.append(s)

    # Add audit-matched terms
    for s in audit_matched:
        if s in SKILL_KB and s not in priority:
            priority.append(s)

    # Fill in remaining from default order
    for s in default_order:
        if s not in priority:
            priority.append(s)

    return priority


def _reorder_experience_for_job(category: str, job_skills: list[str]) -> list[dict]:
    """Reorder experience entries so most relevant come first, based on job skill overlap."""
    job_skills_set = set(s.lower() for s in job_skills)

    scored_entries = []
    for entry in EXPERIENCE_ENTRIES:
        # Score relevance: how many of the job's skills does this experience use?
        relevance = 0
        for s in entry["skills_used"]:
            s_aliases = SKILL_KB.get(s, {}).get("aliases", [s.lower()])
            if any(alias in job_skills_set for alias in s_aliases):
                relevance += 2
            if s.lower() in [j.lower() for j in job_skills]:
                relevance += 1

        # Add category relevance weight
        cat_weight = entry.get("relevance_weights", {}).get(category, 0.5)
        total_score = relevance + cat_weight * 3

        scored_entries.append((total_score, entry))

    # Sort by score descending, then by recency as tiebreaker
    scored_entries.sort(key=lambda x: (-x[0], -x[1]["years_from"]))
    return [entry for _, entry in scored_entries]


def _reorder_bullets_for_job(bullets: list[str], job_skills: list[str]) -> list[str]:
    """Reorder bullets within a role so most relevant come first."""
    job_text = " ".join(job_skills).lower()

    scored_bullets = []
    for bullet in bullets:
        bullet_lower = bullet.lower()
        # Count keyword overlap
        score = sum(1 for skill in job_skills
                    if any(alias in bullet_lower for alias in SKILL_KB.get(skill, {}).get("aliases", [skill.lower()])))
        # Slight bonus for bullets with quantified achievements
        if re.search(r'\d+%|\d+\+|\d+ percent', bullet):
            score += 0.5
        scored_bullets.append((score, bullet))

    scored_bullets.sort(key=lambda x: -x[0])
    return [b for _, b in scored_bullets]


def _generate_tailored_summary(category: str, score_data: dict) -> str:
    """Generate a job-specific professional summary."""
    cfg = CATEGORY_CONFIGS[category]
    matched_skills = score_data.get("matched_skills", [])
    job_skills = [s["skill"] for s in matched_skills]

    if matched_skills:
        top_skills = [s["skill"] for s in matched_skills[:3]]
        skill_phrase = ", ".join(top_skills)
        base = cfg["summary"]
        if base.startswith("Infrastructure and M365"):
            return f"Infrastructure and M365 Engineer with demonstrated expertise in {skill_phrase}. " + base.split(". ", 1)[-1]
        elif base.startswith("Hands-on"):
            return f"Hands-on technician combining enterprise {skill_phrase.lower()} experience with field-based technical work. " + base.split(". ", 1)[-1]
        elif base.startswith("Field-based"):
            return f"Field-based infrastructure professional with {skill_phrase.lower()} background seeking practical work. " + base.split(". ", 1)[-1]
        elif base.startswith("Melbourne-based"):
            return f"Melbourne-based professional with {skill_phrase.lower()} experience seeking a practical local role. " + base.split(". ", 1)[-1]
        else:
            return base
    else:
        return cfg["summary"]


def write_resume(prefix: str, title: str, category: str, reason: str,
                 tags_list: list, audit: dict, score_data: dict = None) -> Path:
    """Generate a dynamically tailored resume for a specific job."""
    if score_data is None:
        score_data = {}

    cfg = CATEGORY_CONFIGS[category]
    matched_skills = score_data.get("matched_skills", [])
    job_skills = [s["skill"] for s in matched_skills]
    audit_matched = audit.get("matched_terms", [])

    # ── Reorder skills ──
    skill_order = _reorder_skills_for_job(category, job_skills, audit_matched)
    skill_display = " · ".join(skill_order)

    # ── Reorder experience ──
    experience_entries = _reorder_experience_for_job(category, job_skills)

    # ── Generate tailored summary ──
    tailored_summary = _generate_tailored_summary(category, score_data)

    # ── Build resume lines ──
    lines = [
        "# Sam Ludwig",
        "Melbourne, VIC | 0405 993 245 | sam.ludwig@gmail.com",
        "samludwig.au | github.com/Ludwixix",
        "",
        f"## Target Role: {title}",
        "",
        "### Professional Summary",
        tailored_summary,
        "",
        "### Profile",
        natural_reason(reason),
        "",
        "### Core Skills",
        skill_display,
        "",
        "### Professional Experience",
    ]

    for experience in experience_entries:
        bullets = experience["bullets_by_category"].get(category, experience["bullets_by_category"].get("core", []))
        # Reorder bullets for this specific job
        if job_skills:
            bullets = _reorder_bullets_for_job(bullets, job_skills)

        lines += [f"### {experience['heading']}", f"{experience['period']} · {experience['location']}"]
        lines += [f"- {bullet}" for bullet in bullets]
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


# ═══════════════════════════════════════════════════════════════════════════
#  3. COMPANY-SPECIFIC COVER LETTER
# ═══════════════════════════════════════════════════════════════════════════

def _determine_tone(role: dict) -> str:
    """Determine cover letter tone based on company type."""
    job_req = _extract_requirements_from_job(role)
    company = (role.get("company") or "").lower()

    if job_req["company_size"] == "government":
        return "formal"
    elif job_req["company_size"] == "enterprise":
        return "professional"
    elif job_req["company_size"] == "msp":
        return "professional"
    elif job_req["company_size"] == "startup":
        return "casual"
    else:
        return "professional"


def _get_company_hook(role: dict) -> str:
    """Generate a company-specific hook referencing mission, products, or context."""
    company = (role.get("company") or "")
    title = (role.get("title") or "")
    why = (role.get("why") or "")
    desc = (role.get("description") or "")

    company_lower = company.lower()

    # Known company hooks
    hooks = {
        "victorian institute of teaching": f"I'm drawn to {company}'s mission of supporting quality teaching across Victoria. Contributing reliable cloud infrastructure to an organisation that directly impacts educational outcomes is meaningful work.",
        "victorian government": f"I'm motivated by the opportunity to contribute to Victorian Government technology infrastructure. Having previously delivered enterprise services in a government environment through the Department of Education Victoria, I understand the scale, security requirements, and public-accountability standards involved.",
        "lgt wealth management": f"I'm interested in contributing to {company}'s technology operations in the wealth management space. Financial services demand precise, security-conscious infrastructure, and my experience across Microsoft 365, Azure, and identity management aligns with the operational standards this sector requires.",
        "amazon": f"I'm drawn to the scale and operational discipline of Amazon's data-centre environment. My background in endpoint support, physical infrastructure, and structured operational procedures connects directly with the demands of a world-class data-centre operation.",
        "first focus it": f"I'm interested in contributing to {company}'s Microsoft-focused technical support operations. My hands-on experience across Azure, Active Directory, Outlook, and customer-facing troubleshooting aligns with the service-delivery standards your clients expect.",
        "converged medical solutions": f"I'm attracted to {company}'s focus on cybersecurity and Microsoft 365 solutions for healthcare organisations. My experience delivering enterprise services in hospital environments through St John of God Health Care gives me direct familiarity with the reliability and compliance standards healthcare technology demands.",
        "fujifilm microchannel": f"I'm interested in contributing to {company}'s Azure cloud consulting practice. My Azure, Microsoft 365, identity management, and customer-facing technical delivery experience aligns with the consultancy context and cloud-solutions focus.",
    }

    # Check for exact or partial company match
    for key, hook in hooks.items():
        if key in company_lower:
            return hook

    # Generic fallback based on sector
    if any(w in company_lower for w in ["health", "hospital", "medical", "clinical"]):
        return f"I'm motivated by the opportunity to support healthcare technology at {company}. My experience delivering infrastructure in clinical environments means I understand the zero-disruption standards healthcare demands."
    elif any(w in company_lower for w in ["education", "school", "university"]):
        return f"I'm drawn to {company}'s educational mission. Having previously supported government education technology at scale, I understand the unique demands of education-sector IT."
    elif any(w in company_lower for w in ["bank", "finance", "wealth", "insurance"]):
        return f"I'm interested in contributing to {company}'s technology operations. Financial services demand precise, security-conscious infrastructure, and my enterprise experience aligns with those standards."

    return f"I'm writing to express my interest in the {title} role at {company}. My background across enterprise infrastructure, Microsoft 365, and service operations connects well with the requirements outlined."


def _generate_achievement_bullets(matched_skills: list, max_bullets: int = 3) -> list[str]:
    """Generate quantified achievement bullets that match the role's requirements."""
    bullets = []

    # Map skills to specific achievements
    achievement_map = {
        "Microsoft 365": "Delivered enterprise Microsoft 365 services across SharePoint, Exchange, Teams, and Entra ID for 660,000+ users",
        "SharePoint": "Managed the Southern Hemisphere's largest SharePoint farm with 660,000+ users and 99.9% uptime",
        "Azure": "Spearheaded Azure cloud adoption aligned with ACSC Essential 8 maturity model requirements",
        "Entra ID": "Managed hybrid identity synchronisation across three identity providers for 660,000+ users",
        "Intune": "Led Windows 11 migration across 100+ clinical endpoints with zero patient-care disruption",
        "PowerShell": "Built PowerShell automation reducing migration processing time by 87% (2 hours to 15 minutes)",
        "Exchange": "Administered Exchange Hybrid environment resolving complex mail-flow, calendar, and federation issues",
        "Teams": "Delivered enterprise Teams rollout with governance, meeting policies, and federation management",
        "Windows": "Managed Windows 10/11 migrations and standardised SOE builds across enterprise fleets",
        "Autopilot": "Achieved 100% Autopilot adherence in clinical Windows 11 migration across 100+ endpoints",
        "ServiceNow": "Built ServiceNow automation eliminating hundreds of hours of manual data entry per month",
        "Active Directory": "Managed Active Directory and Group Policy for enterprise environments supporting 660,000+ users",
        "Security": "Aligned infrastructure with ACSC Essential 8 and implemented MFA compliance across 200+ sites",
        "Documentation": "Produced RCA reports that reduced repeat incidents by 15% over 12 months",
        "Customer Support": "Delivered L1/L2/L3 support consistently achieving >90% SLA resolution",
        "Network": "Deployed fibre and copper Layer 1 infrastructure across residential and commercial environments",
        "HVAC": "Installed, maintained, and repaired commercial HVAC systems with systematic fault-finding",
    }

    for skill in matched_skills:
        skill_name = skill.get("skill", "")
        if skill_name in achievement_map and len(bullets) < max_bullets:
            bullets.append(achievement_map[skill_name])

    # Fallback if no specific matches
    if not bullets:
        bullets = [
            "Delivered enterprise infrastructure support across Azure, Microsoft 365, and identity platforms",
            "Built PowerShell automation solutions that eliminated recurring manual toil",
            "Led root-cause analysis investigations with documented 15% reduction in repeat incidents",
        ]

    return bullets[:max_bullets]


def _to_noun_phrase(achievement: str) -> str:
    """Transform a past-tense achievement into a noun phrase for smoother reading."""
    achievement = achievement.strip()
    verb_map = [
        ("Delivered", "experience delivering"),
        ("Managed", "experience managing"),
        ("Built", "experience building"),
        ("Led", "experience leading"),
        ("Spearheaded", "experience spearheading"),
        ("Administered", "experience administering"),
        ("Deployed", "experience deploying"),
        ("Engineered", "experience engineering"),
        ("Oversaw", "experience overseeing"),
        ("Implemented", "experience implementing"),
        ("Supported", "experience supporting"),
        ("Resolved", "experience resolving"),
        ("Acted", "experience acting"),
        ("Produced", "experience producing"),
        ("Configured", "experience configuring"),
    ]
    for verb, phrase in verb_map:
        if achievement.startswith(verb):
            # Lowercase the first letter of the remainder
            remainder = achievement[len(verb):]
            return phrase + remainder[0].lower() + remainder[1:]
    # Fallback: just lowercase the whole thing
    return achievement[0].lower() + achievement[1:]


def write_cover(prefix: str, role: dict, category: str, reason: str,
                tags_list: list, audit: dict, score_data: dict = None) -> Path:
    """Generate a company-specific, requirement-aware cover letter."""
    if score_data is None:
        score_data = {}

    title = role["title"]
    company = employer_name(role)
    location = role["location"]
    tone = _determine_tone(role)
    matched_skills = score_data.get("matched_skills", [])
    missing_skills = score_data.get("missing_skills", [])

    # ── Opening ──
    if tone == "formal":
        salutation = "Dear Hiring Manager,"
        opening = f"I am writing to express my interest in the {title} position at {company}."
    elif tone == "casual":
        salutation = "Hi there,"
        opening = f"I'd love to be considered for the {title} role at {company}."
    else:
        salutation = "Dear Hiring Manager,"
        opening = f"I'm writing to express my interest in the {title} position with {company}."

    # ── Company hook ──
    company_hook = _get_company_hook(role)

    # ── Why this role ──
    why_role = natural_reason(reason)

    # ── Achievement paragraph ──
    achievement_bullets = _generate_achievement_bullets(matched_skills, max_bullets=3)
    achievement_para = "I bring ";
    def _to_phrase(text):
        """Convert a past-tense achievement bullet to a natural noun phrase."""
        prefixes = [
            ("Delivered", "delivering"),
            ("Managed", "managing"),
            ("Built", "building"),
            ("Led", "leading"),
            ("Spearheaded", "spearheading"),
            ("Administered", "administering"),
            ("Deployed", "deploying"),
            ("Implemented", "implementing"),
            ("Provided", "providing"),
            ("Resolved", "resolving"),
        ]
        for past, gerund in prefixes:
            if text.startswith(past):
                return gerund + text[len(past):]
        return text.lower()

    if len(achievement_bullets) == 1:
        first = achievement_bullets[0]
        # For a single bullet, use "experience" + gerund form for smoother reading
        prefixes = [
            ("Delivered", "delivering"),
            ("Managed", "managing"),
            ("Built", "building"),
            ("Led", "leading"),
            ("Spearheaded", "spearheading"),
            ("Administered", "administering"),
            ("Deployed", "deploying"),
            ("Implemented", "implementing"),
            ("Provided", "providing"),
            ("Resolved", "resolving"),
        ]
        transformed = False
        for past, gerund in prefixes:
            if first.startswith(past):
                achievement_para += f"experience {gerund}" + first[len(past):] + "."
                transformed = True
                break
        if not transformed:
            achievement_para += first.lower() + "."
    elif len(achievement_bullets) == 2:
        achievement_para += "experience " + _to_phrase(achievement_bullets[0]) + " and " + _to_phrase(achievement_bullets[1]) + "."
    else:
        achievement_para += "experience " + _to_phrase(achievement_bullets[0]) + ", " + _to_phrase(achievement_bullets[1]) + ", and " + _to_phrase(achievement_bullets[2]) + "."

    # ── Skills match paragraph ──
    if matched_skills:
        skill_names = [s["skill"] for s in matched_skills[:5]]
        skills_para = f"The areas where my experience aligns most directly with this role are {', '.join(skill_names)}."
    else:
        skills_para = f"The areas most relevant to the role are {', '.join(tags_list[:3]).lower()}."

    # ── Address gaps if any critical ones ──
    critical_missing = [s for s in missing_skills if s["severity"] == "critical"]
    gap_note = ""
    if critical_missing:
        gap_note = f"\n\nI should note that while I bring strong experience across the core requirements, I would develop my {critical_missing[0]['skill'].lower()} capabilities further in this role. My track record of rapid skill acquisition — including picking up PowerShell automation and Azure cloud operations on the job — gives me confidence I can bridge any gaps quickly."

    # ── Closing ──
    if tone == "formal":
        closing = "I would welcome the opportunity to discuss how my experience could contribute to your team. I am available for an interview at your convenience and happy to confirm any licence, qualification, or screening requirements before progressing."
        sign_off = "Yours sincerely,"
    elif tone == "casual":
        closing = "I'd love to chat about how my background could help the team. Happy to jump on a call whenever suits."
        sign_off = "Cheers,"
    else:
        closing = "I'd welcome a conversation about how my background could contribute to your team. I'm happy to confirm any licence, qualification, check, roster or prior-industry requirements before progressing."
        sign_off = "Kind regards,"

    # ── Assemble ──
    body = [
        "# Sam Ludwig",
        "Melbourne, VIC | 0405 993 245 | sam.ludwig@gmail.com",
        "",
        f"**Re: {title} — {company}**",
        "",
        salutation,
        "",
        f"{opening} {company_hook}",
        "",
        why_role,
        "",
        f"{achievement_para}",
        "",
        f"{skills_para}{gap_note}",
        "",
        closing,
        "",
        sign_off,
        "Sam Ludwig",
    ]

    path = APP / f"{prefix}_cover_letter.md"
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return path


# ═══════════════════════════════════════════════════════════════════════════
#  Supporting functions (kept from original where stable)
# ═══════════════════════════════════════════════════════════════════════════

def employer_name(role):
    company = (role.get("company") or "").strip()
    title = (role.get("title") or "").strip()
    return "your organisation" if not company or company.casefold() == title.casefold() else company


def natural_reason(reason):
    reason = re.sub(r"^Your .*? opportunity (is|matches|aligns with|combines)", r"This role \1", reason)
    # Clean up raw listing descriptions that aren't actual reasons
    reason = re.sub(r"^(Adzuna|Indeed|SEEK|Jora|Glassdoor) listing for .+", r"", reason)
    reason = re.sub(r"^(Individual|Current) (Indeed|listing) for .+", r"", reason)
    replacements = {
        "This is one of the closest matches to my recent endpoint and service-desk work.": "The work is a close match for my recent endpoint and service-desk experience.",
        "This is a deliberate career-change application.": "I'm making a deliberate move into this kind of practical work.",
        "This is a deliberate local career-change application.": "I'm making a deliberate move into local practical work.",
        "This is a local-work transition application.": "I'm looking for a practical local role.",
        "The master résumé does not claim commercial kitchen experience, so this pack focuses only on transferable reliability, service operations, learning ability and structured work.": "I haven't worked in a commercial kitchen, but I'm used to reliable procedures, service operations, learning new systems and taking responsibility for the work in front of me.",
        "I do not claim a Cert III in Horticulture or prior commercial gardening experience.": "I don't hold a Cert III in Horticulture and haven't worked in commercial gardening.",
        "I do not claim parks, conservation or ranger experience, so the position requirements need careful review.": "I haven't worked in parks, conservation or a ranger role, so I'd want to confirm the position requirements.",
        "I do not claim brushcutter or horticulture qualifications.": "I don't hold brushcutter or horticulture qualifications.",
        "I do not claim horticultural qualifications, so the role's exact requirements need verification.": "I don't hold horticultural qualifications, so I'd want to confirm the role's exact requirements.",
        "no automotive qualification is claimed.": "I don't hold an automotive qualification yet.",
        "no panel-beating qualification is claimed.": "I don't hold a panel-beating qualification yet.",
        "no electrical licence or current electrical apprenticeship stage is claimed.": "I don't hold an electrical licence and I'm not currently in an electrical apprenticeship.",
        "I do not claim barista, bartending or RSA experience; the application focuses on transferable customer service, calm problem-solving and willingness to learn the venue's procedures.": "I haven't worked as a barista or bartender and don't hold an RSA, but I bring customer service experience, calm problem-solving and a willingness to learn your procedures.",
        "I do not claim housekeeping experience, but I bring disciplined procedures, attention to equipment and inventory, service schedules, documentation and reliable task ownership.": "I haven't worked in housekeeping, but I'm comfortable following detailed procedures, working to schedules, looking after equipment and taking ownership of a task.",
        "I do not claim prior medical-reception experience.": "I haven't worked as a medical receptionist before.",
        "The listing is older, so availability must be checked first.": "The listing appears older, so I'd confirm that the position is still available first.",
        "The advertised car and licence requirement must be confirmed.": "I'd need to confirm the advertised car and licence requirement.",
        "The Year 3–4 requirement must be screened first.": "I'd need to confirm the Year 3–4 requirement before applying.",
        "The listing specifies Year 3–4 apprentices, which must be confirmed before applying.": "The listing mentions Year 3–4 apprentices, so I'd confirm that requirement before applying.",
        "The role's exact requirements need verification.": "I'd want to confirm the role's exact requirements.",
        "This targeted résumé uses only experience and qualifications recorded in the master résumé. It does not claim role-specific licences, trade certificates, horticulture qualifications, hospitality experience, or clearances that are not recorded there.": "",
    }
    for old, new in replacements.items():
        reason = reason.replace(old, new)
    return reason.strip()


def experience_year(item):
    match = re.search(r"(20\d{2})", item.get("period", ""))
    return int(match.group(1)) if match else 0


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


def build_audit(role, category, reason, tags_list, score_data=None):
    """Build audit JSON with enhanced scoring data."""
    if score_data is None:
        score_data = {}

    target = " ".join([
        role.get("title", ""), role.get("company", ""), role.get("why", ""),
        " ".join(role.get("tags", [])), " ".join(tags_list), reason,
    ]).lower()
    candidate = master.lower()
    matched = [term for term, aliases in TERM_ALIASES.items()
               if any(alias in target for alias in aliases) and any(alias in candidate for alias in aliases)]
    requested = [term for term, aliases in TERM_ALIASES.items()
                 if any(alias in target for alias in aliases)]
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

    # Use enhanced scoring for fit label
    fit_label = score_data.get("fit_label", "Partial fit")
    score_val = score_data.get("score", 0)

    return {
        "audit_version": "2.0",
        "fit": fit_label,
        "score": score_val,
        "dimensions": score_data.get("dimensions", {}),
        "matched_skills": [s["skill"] for s in score_data.get("matched_skills", [])],
        "missing_skills": score_data.get("missing_skills", []),
        "strengths": score_data.get("strengths", []),
        "risks": score_data.get("risks", []),
        "confidence": score_data.get("confidence", 0.5),
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
            "Read the tailored documents once and edit any wording that doesn't sound like you.",
            "Confirm every licence, qualification, clearance, vehicle, and work-right requirement.",
            "Submit manually only after your explicit approval.",
        ],
        "source_basis": "Role title, listing metadata, job description analysis, skill matching, and verified candidate profile",
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


def write_email(prefix, role, category, reason, tags_list, audit, score_data=None):
    if score_data is None:
        score_data = {}
    contact = CONTACTS.get(role["title"], {})
    email = contact.get("email")
    phone = contact.get("phone")
    manager = contact.get("manager")
    company = employer_name(role)
    matched_skills = score_data.get("matched_skills", [])
    skill_names = [s["skill"] for s in matched_skills[:3]] if matched_skills else tags_list[:3]

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
        f"I'm writing about the {role['title']} position with {company}. {natural_reason(reason)}",
        "",
        "My background includes enterprise technical support, endpoint lifecycle management, field infrastructure, systematic fault-finding, customer communication and process-focused documentation.",
        "",
        f"The areas most relevant to the role are {', '.join(skill_names).lower()}.",
        "",
        "I'd welcome a brief conversation about the role and any position-specific requirements.",
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


# ═══════════════════════════════════════════════════════════════════════════
#  ROLE OVERRIDES & CONTACTS
# ═══════════════════════════════════════════════════════════════════════════

ROLE_OVERRIDES = {
    "Support Technician": ("technician", "The cardioscan role is a strong local fit for my recent endpoint and service-desk work. The Camberwell location and one-day work-from-home arrangement also make it practical from St Kilda.", ["L1/L2 support", "Windows and endpoint support", "MedTech", "Camberwell"]),
    "IT Support Technician": ("technician", "The Microcel role matches my endpoint support, Windows, hardware and school-technology experience. The part-time structure and nearby Cheltenham or Hawthorn East locations make it a practical option.", ["School technology", "Windows support", "Hardware troubleshooting", "Part-time"]),
    "Technical Assistant/ICT Classroom Support": ("technician", "The education-sector ICT classroom-support role is a strong match for my endpoint deployment, hardware troubleshooting, user communication and school-environment experience.", ["Education", "ICT support", "Windows endpoints", "Southern suburbs"]),
    "Service Desk Technician": ("technician", "The Oakleigh service-desk role matches my recent L1/L2 endpoint support, Windows troubleshooting, incident handling, hardware diagnostics and customer communication experience.", ["Service desk", "Windows support", "Endpoint troubleshooting", "Oakleigh"]),
    "Intermediate Service Desk Technician": ("technician", "The intermediate service-desk role aligns with my L1/L2/L3 support background, Microsoft endpoint experience, troubleshooting discipline and service-operations documentation.", ["Service desk", "L1/L2 support", "Microsoft endpoints", "Remote available"]),
    "Engineering Operations Technician": ("technician", "The data-centre engineering-operations role is a credible practical infrastructure pathway. My endpoint, telecommunications and HVAC backgrounds provide relevant equipment, fault-finding and operational-procedure experience; clearance requirements must be confirmed.", ["Data centre", "Engineering operations", "Infrastructure", "Clearance check"]),
    "Microsoft M365 Systems Administrator": ("core", "The Visy Microsoft 365 Systems Administrator role is a strong match for my enterprise M365, identity, security, compliance, automation and platform-operations background.", ["Microsoft 365", "Security and compliance", "PowerShell", "Platform optimisation"]),
    "Senior Systems Engineer": ("core", "The St Vincent's Senior Systems Engineer role aligns with my Microsoft cloud, endpoint, identity, healthcare-continuity, escalation and infrastructure-operations experience.", ["Healthcare infrastructure", "Microsoft cloud", "Systems engineering", "Service operations"]),
    "Group Infrastructure Engineer": ("core", "The Icon Group Infrastructure Engineer role matches my enterprise infrastructure, Microsoft 365, Azure, endpoint, automation and transformation experience.", ["Infrastructure", "Modernisation", "Azure", "Transformation"]),
    "Systems Administrator": ("core", "The DYSON GROUP Systems Administrator role matches my Windows, Microsoft 365, endpoint, identity, automation and user-support experience in a permanent operational environment.", ["Systems administration", "Windows", "Microsoft 365", "User support"]),
    "Site Support Senior Technician": ("technician", "The Computershare site-support role matches my endpoint diagnostics, Windows support, user communication, asset handling and enterprise service-operations experience.", ["Site support", "Endpoint support", "Enterprise", "Troubleshooting"]),
    "Senior DevOps Engineer": ("core", "The FMClarity Senior DevOps Engineer role is a stretch toward DevOps, but its Melbourne SaaS environment, cloud operations, automation and service-improvement focus align with my infrastructure background.", ["Cloud operations", "Automation", "SaaS", "Infrastructure"]),
    "Infrastructure Engineer – Telecommunications and IT": ("technician", "The Socia Infrastructure Engineer role connects my NBN telecommunications field background with enterprise infrastructure support across network, compute, storage and service operations.", ["Telecommunications", "Infrastructure", "Networking", "Contract"]),
    "Shift Technician- Air Conditioning & Refrigeration, Data Center": ("technician", "The CBRE data-centre shift-technician role uses my earlier HVAC service experience, practical fault-finding and equipment-handling background. I would confirm the rotating 12-hour roster and trade requirements first.", ["HVAC", "Data centre", "Rotating roster", "Field service"]),
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
    "Maintenance / Groundskeeper": ("outdoor", "My field service, HVAC maintenance and site-assessment experience provides transferable grounds and facilities support skills. I do not claim horticultural qualifications, so the role's exact requirements need verification.", ["Groundskeeping", "Facilities", "Southern suburbs", "Requirement check"]),
    "Panel Beater & Apprentice Spray Painter": ("local", "This is a local practical-work application with an advertised apprentice-to-leadership pathway. My transferable experience comes from HVAC and telecommunications fault-finding; no panel-beating qualification is claimed.", ["St Kilda", "Apprenticeship", "Workshop", "Career change"]),
    "Part-Time Customer Service and Sales Assistant": ("local", "The St Kilda location and small part-time commitment make this a practical local option. My experience includes customer-facing technical support, clear explanations, stock and asset control, and dependable service operations.", ["St Kilda", "Part-time", "Customer service", "Asset control"]),
    "Casual Housekeeper": ("local", "This is a local-work transition application. I do not claim housekeeping experience, but I bring disciplined procedures, attention to equipment and inventory, service schedules, documentation and reliable task ownership.", ["St Kilda", "Casual", "Local work", "Transferable skills"]),
    "Cook / Chef / Kitchen Staff": ("local", "This is a deliberate local career-change application. The master résumé does not claim commercial kitchen experience, so this pack focuses only on transferable reliability, service operations, learning ability and structured work.", ["St Kilda", "Part-time", "Career change", "Training needed"]),
    "Retail Planogram Merchandiser — Casual": ("local", "The role's local, field-based and inventory-oriented structure connects with my asset-control, site-assessment, documentation and customer-facing support experience. The advertised car and licence requirement must be confirmed.", ["St Kilda", "Casual", "Inventory", "Car/licence check"]),
    "Barista / Bartender": ("local", "This is a deliberate local hospitality application. I do not claim barista, bartending or RSA experience; the application focuses on transferable customer service, calm problem-solving and willingness to learn the venue's procedures.", ["St Kilda", "Part-time", "Hospitality", "RSA check"]),
    "Team Member": ("local", "The listing says no experience is needed and highlights training. My recent support roles demonstrate customer communication, reliable procedures, teamwork, queue management and the ability to learn systems quickly.", ["St Kilda", "Training", "Customer service", "Entry-level"]),
    "LEGO Robotics and Science Tutor / Instructor": ("local", "This is the strongest local non-infrastructure match because it combines technical communication, client workshops, automation projects and explaining complex concepts to non-technical audiences.", ["South Melbourne", "STEM", "Technical communication", "Part-time"]),
    "Medical Receptionist — Part-time": ("local", "My service-centre and healthcare project experience provides transferable customer communication, scheduling, documentation, privacy-conscious support and clinical-environment familiarity. I do not claim prior medical-reception experience.", ["St Kilda East", "Part-time", "Healthcare environment", "Experience check"]),
}

CONTACTS = {
    # No direct hiring contacts were published in the retrieved role records.
}

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
    "EUC Engineer": "Your EUC Engineer opportunity matches my hands-on endpoint delivery across Intune, Autopilot, Windows 10/11, application deployment, compliance, diagnostics and lifecycle management.",
    "End User Services Engineer VIC (Intune MDM, Kandji)": "Your End User Services Engineer opportunity matches my combination of Microsoft 365, Intune, Windows 11, Autopilot, endpoint lifecycle and customer-facing managed-services support.",
    "IT Systems Administrator": "Your IT Systems Administrator opportunity combines the internal IT ownership and systems improvement work that fits my Microsoft 365, Azure, Entra ID, endpoint, ServiceNow and automation background.",
    "Engineer - Modern Workplace (Managed Services)": "Your Modern Workplace Engineer opportunity matches my Microsoft 365, Intune, Autopilot, Windows, Entra ID, automation and managed-services escalation experience.",
    "Cloud Engineer (Level 2)": "Your Level 2 Cloud Engineer opportunity aligns with my Azure, Microsoft 365, Entra ID, endpoint and escalation experience, supported by PowerShell, Graph and ITIL 4 practices.",
    "Service Desk Engineer": "Your Service Desk Engineer opportunity matches my recent L1/L2/L3 support, hardware diagnostics, Windows imaging, Autopilot/UEM, ServiceNow automation and endpoint lifecycle experience. I understand that a short video response is already pending in the existing process.",
    "Engineering Operations Technician, Data Center Engineering Operations": "The Amazon data-centre engineering-operations role matches my endpoint support, physical infrastructure, fault-finding, operational procedures, and data-centre exposure. The structured, safety-conscious environment aligns with my disciplined approach to technical operations.",
    "Engineering Operations Technician": "The data-centre engineering-operations role matches my endpoint support, physical infrastructure, fault-finding, operational procedures, and data-centre exposure.",
}


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN GENERATION LOOP
# ═══════════════════════════════════════════════════════════════════════════

# Direct role additions (kept from original)
DIRECT_ROLE_ADDITIONS = [
    {
        "rank": 0, "score": 93, "company": "Victorian Institute of Teaching",
        "title": "Senior Cloud Engineer", "location": "Melbourne CBD and inner metro suburbs",
        "posted": "2026-08-03", "source": "Careers Vic",
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
        "rank": 0, "score": 91, "company": "First Focus IT",
        "title": "Tech Support roles", "location": "Melbourne, VIC",
        "posted": "2026-08-07", "source": "Indeed",
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
        "rank": 0, "score": 89, "company": "Converged Medical Solutions",
        "title": "Computer Network and Systems Engineer", "location": "Carrum Downs, VIC / remote available",
        "posted": "2026-08-03", "source": "Indeed",
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
        "rank": 0, "score": 87, "company": "FUJIFILM MicroChannel",
        "title": "Microsoft Cloud Solutions Consultant", "location": "Melbourne, VIC / hybrid",
        "posted": "2026-07-28", "source": "Indeed",
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
        "rank": 0, "score": 82, "company": "Amazon.com",
        "title": "Data Center IT Support Engineer, MEL - DCO", "location": "Melbourne, VIC",
        "posted": "2026-07-27", "source": "Indeed",
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
        "rank": 0, "score": 94, "company": "LGT Wealth Management Australia",
        "title": "Infrastructure Engineer", "location": "Melbourne, VIC",
        "posted": "2026-07-25", "source": "LGT Careers",
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
        "rank": 0, "score": 92, "company": "Victorian Government",
        "title": "Senior Cloud Engineer", "location": "Melbourne CBD and inner metro suburbs",
        "posted": "2026-08-04", "source": "Careers Vic",
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

# Fix employer names
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


# ── Generate for all jobs ──
count_new = 0
count_emails = 0

for role in data["jobs"]:
    # Determine reason
    if role.get("company") == "LGT Wealth Management Australia":
        reason = "The LGT Infrastructure Engineer role is a strong match for my experience across Windows, Azure, Microsoft 365, Entra ID, PowerShell automation, incident response, documentation, and production support."
    elif role.get("company") == "Victorian Institute of Teaching":
        reason = "The Victorian Institute of Teaching Senior Cloud Engineer role matches my Azure, Microsoft 365, Entra ID, hybrid identity, automation, enterprise support, and public-sector delivery experience."
    elif role.get("company") == "Victorian Government":
        reason = "The Victorian Government Senior Cloud Engineer role matches my Azure, Microsoft 365, identity, automation, enterprise support, and public-sector delivery experience."
    else:
        reason = CORE_EMAILS.get(role["title"], role["why"])

    tags_list = ["Core infrastructure", "Tailored existing materials", "Verify listing"]

    # Determine prefix
    existing_resume = role.get("resume", "")
    if role.get("company") == "Victorian Institute of Teaching":
        prefix = filename_prefix(role)
    else:
        prefix = Path(existing_resume).stem.removesuffix("_resume") if existing_resume else filename_prefix(role)

    # ── Score the job ──
    score_data = score_job(role, "core")

    # ── Build audit ──
    audit = build_audit(role, "core", reason, tags_list, score_data)
    audit_path = AUDITS / f"{prefix}_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ── Generate materials ──
    resume_path = write_resume(prefix, role["title"], "core", reason, tags_list, audit, score_data)
    cover_path = write_cover(prefix, role, "core", reason, tags_list, audit, score_data)
    email_path = write_email(prefix, role, "core", reason, tags_list, audit, score_data)
    attach_paths(role, prefix, resume_path, cover_path, email_path, audit_path)

    # ── Attach scoring data to role ──
    role["scoring"] = {
        "score": score_data["score"],
        "fit_label": score_data["fit_label"],
        "dimensions": score_data["dimensions"],
        "matched_skills": [s["skill"] for s in score_data["matched_skills"]],
        "missing_skills": score_data["missing_skills"],
        "strengths": score_data["strengths"],
        "risks": score_data["risks"],
        "confidence": score_data["confidence"],
    }

    count_emails += 1

# Generate for sections
for category, roles in data.get("sections", {}).items():
    for role in roles:
        override = ROLE_OVERRIDES.get(role["title"])
        if not override:
            raise RuntimeError(f"No tailoring profile exists for new role: {role['title']}")
        cat, reason, tags_list = override

        # ── Score the job ──
        score_data = score_job(role, cat)

        prefix = filename_prefix(role)
        audit = build_audit(role, cat, reason, tags_list, score_data)
        audit_path = AUDITS / f"{prefix}_audit.json"
        audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        resume_path = write_resume(prefix, role["title"], cat, reason, tags_list, audit, score_data)
        cover_path = write_cover(prefix, role, cat, reason, tags_list, audit, score_data)
        email_path = write_email(prefix, role, cat, reason, tags_list, audit, score_data)
        attach_paths(role, prefix, resume_path, cover_path, email_path, audit_path)

        # Attach scoring data
        role["scoring"] = {
            "score": score_data["score"],
            "fit_label": score_data["fit_label"],
            "dimensions": score_data["dimensions"],
            "matched_skills": [s["skill"] for s in score_data["matched_skills"]],
            "missing_skills": score_data["missing_skills"],
            "strengths": score_data["strengths"],
            "risks": score_data["risks"],
            "confidence": score_data["confidence"],
        }

        count_new += 1
        count_emails += 1

# ── Write application pack index ──
data["updated"] = datetime.now().astimezone().isoformat()
data["search_area"] = "Melbourne, St Kilda area, and remote Australia"
data["policy"] = "LinkedIn excluded. Individual listings and direct employer or government routes are preferred. Search-only sources are labelled and must be verified manually. No applications or emails are submitted automatically."

index = []
for role in data["jobs"]:
    scoring = role.get("scoring", {})
    index.append({
        "lane": "core",
        "company": role["company"],
        "title": role["title"],
        "location": role["location"],
        "source": role.get("source"),
        "application_route": role.get("application_route", role.get("url")),
        "application_route_type": role.get("application_route_type"),
        "listing_verification": role.get("listing_verification"),
        "application_url": role["url"],
        "resume": role.get("resume"),
        "cover": role.get("cover"),
        "resume_source": role.get("resume_md"),
        "cover_source": role.get("cover_md"),
        "opening_email": role.get("email_md"),
        "audit": role.get("audit_json"),
        "fit": scoring.get("fit_label", role.get("audit", {}).get("fit")),
        "score": scoring.get("score", 0),
        "dimensions": scoring.get("dimensions", {}),
        "matched_skills": scoring.get("matched_skills", []),
        "missing_skills": scoring.get("missing_skills", []),
        "strengths": scoring.get("strengths", []),
        "risks": scoring.get("risks", []),
        "confidence": scoring.get("confidence", 0.5),
        "matched_terms": role.get("audit", {}).get("matched_terms", []),
        "gaps": role.get("audit", {}).get("unsupported_or_unverified_terms", []),
        "requirements_to_confirm": role.get("audit", {}).get("requirements_to_confirm", []),
        "contact_email": role.get("contact_email"),
        "contact_phone": role.get("contact_phone"),
        "hiring_manager": role.get("hiring_manager"),
    })

for category, roles in data.get("sections", {}).items():
    for role in roles:
        scoring = role.get("scoring", {})
        index.append({
            "lane": category,
            "company": role["company"],
            "title": role["title"],
            "location": role["location"],
            "source": role.get("source"),
            "application_route": role.get("application_route", role.get("url")),
            "application_route_type": role.get("application_route_type"),
            "listing_verification": role.get("listing_verification"),
            "application_url": role["url"],
            "resume": role.get("resume"),
            "cover": role.get("cover"),
            "resume_source": role.get("resume_md"),
            "cover_source": role.get("cover_md"),
            "opening_email": role.get("email_md"),
            "audit": role.get("audit_json"),
            "fit": scoring.get("fit_label", role.get("audit", {}).get("fit")),
            "score": scoring.get("score", 0),
            "dimensions": scoring.get("dimensions", {}),
            "matched_skills": scoring.get("matched_skills", []),
            "missing_skills": scoring.get("missing_skills", []),
            "strengths": scoring.get("strengths", []),
            "risks": scoring.get("risks", []),
            "confidence": scoring.get("confidence", 0.5),
            "matched_terms": role.get("audit", {}).get("matched_terms", []),
            "gaps": role.get("audit", {}).get("unsupported_or_unverified_terms", []),
            "requirements_to_confirm": role.get("audit", {}).get("requirements_to_confirm", []),
            "contact_email": role.get("contact_email"),
            "contact_phone": role.get("contact_phone"),
            "hiring_manager": role.get("hiring_manager"),
        })

(ROOT / "application_pack_index.json").write_text(
    json.dumps({"generated": data["updated"], "applications_submitted": False, "roles": index},
               indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8"
)

DATA_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"Generated tailored CVs and cover letters for {count_new} new roles")
print(f"Generated opening emails for {count_emails} roles")
print(f"Wrote application_pack_index.json with {len(index)} roles")
print(f"\nScoring system: v2.0 with multi-dimensional analysis")
print(f"Resume system: dynamic reorder by job requirements")
print(f"Cover letter system: company-specific, requirement-aware")
