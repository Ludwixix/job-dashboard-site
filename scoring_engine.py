#!/usr/bin/env python3
"""
Enhanced Job Suitability Scoring Engine v2
Multi-dimensional fit analysis with gap detection and confidence scoring.
Integrated with the existing generate_all_application_materials.py.
"""
import json
import re
from pathlib import Path

# Sam's profile loaded from job_profile.json
PROFILE_PATH = Path(__file__).parent / "job_profile.json"

def load_profile() -> dict:
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ─── Skill Database ───────────────────────────────────────────────────────────
# Maps skill names to Sam's proficiency and years of experience
SKILL_DB = {
    # Cloud & M365
    "azure": {"level": "advanced", "years": 4, "category": "cloud", "aliases": ["azure", "microsoft azure", "azure ad", "entra"]},
    "microsoft 365": {"level": "expert", "years": 6, "category": "cloud", "aliases": ["m365", "microsoft 365", "modern workplace", "office 365"]},
    "sharepoint": {"level": "expert", "years": 6, "category": "cloud", "aliases": ["sharepoint", "sharepoint online", "spo"]},
    "exchange": {"level": "advanced", "years": 5, "category": "cloud", "aliases": ["exchange", "exchange online", "exchange hybrid", "email"]},
    "teams": {"level": "advanced", "years": 4, "category": "cloud", "aliases": ["teams", "microsoft teams"]},
    "intune": {"level": "advanced", "years": 3, "category": "endpoint", "aliases": ["intune", "endpoint manager", "euc", "mdm"]},
    "autopilot": {"level": "advanced", "years": 3, "category": "endpoint", "aliases": ["autopilot", "windows autopilot"]},
    "entra id": {"level": "advanced", "years": 4, "category": "identity", "aliases": ["entra", "entra id", "azure ad", "active directory", "ad ds", "hybrid identity"]},
    "active directory": {"level": "advanced", "years": 5, "category": "identity", "aliases": ["active directory", "ad", "ad ds", "gpo"]},

    # Scripting & Automation
    "powershell": {"level": "expert", "years": 6, "category": "automation", "aliases": ["powershell", "pwsh", "automation"]},
    "python": {"level": "intermediate", "years": 3, "category": "automation", "aliases": ["python", "python3"]},

    # Infrastructure
    "windows": {"level": "expert", "years": 8, "category": "os", "aliases": ["windows", "windows 10", "windows 11", "windows server"]},
    "linux": {"level": "basic", "years": 1, "category": "os", "aliases": ["linux", "ubuntu", "centos", "redhat"]},
    "vmware": {"level": "basic", "years": 1, "category": "virtualization", "aliases": ["vmware", "vsphere", "esxi"]},

    # Networking
    "networking": {"level": "intermediate", "years": 3, "category": "network", "aliases": ["network", "networking", "tcp/ip", "dns", "dhcp", "vpn"]},
    "layer 1": {"level": "intermediate", "years": 2, "category": "physical", "aliases": ["layer 1", "l1", "cabling", "fibre", "fiber", "copper"]},

    # ITSM & Process
    "servicenow": {"level": "advanced", "years": 3, "category": "itsm", "aliases": ["servicenow", "service now"]},
    "itil": {"level": "intermediate", "years": 4, "category": "itsm", "aliases": ["itil", "incident management", "problem management", "change management"]},

    # Security
    "cybersecurity": {"level": "basic", "years": 2, "category": "security", "aliases": ["cybersecurity", "security", "infosec", "essential 8", "iso 27001"]},

    # Physical
    "hvac": {"level": "intermediate", "years": 2, "category": "physical", "aliases": ["hvac", "air conditioning", "refrigeration", "thermal"]},
    "data centre": {"level": "intermediate", "years": 2, "category": "physical", "aliases": ["data centre", "data center", "server room", "rack"]},

    # Soft Skills
    "customer service": {"level": "advanced", "years": 6, "category": "soft", "aliases": ["customer service", "customer support", "user support", "help desk"]},
    "documentation": {"level": "expert", "years": 6, "category": "soft", "aliases": ["documentation", "technical writing", "runbooks"]},
    "stakeholder management": {"level": "advanced", "years": 4, "category": "soft", "aliases": ["stakeholder", "communication", "workshop"]},
    "team leadership": {"level": "intermediate", "years": 3, "category": "soft", "aliases": ["leadership", "mentoring", "team lead"]},
}

# ─── Experience Levels ────────────────────────────────────────────────────────
EXPERIENCE_LEVELS = {
    "junior": {"min_years": 0, "max_years": 2, "title_patterns": ["junior", "graduate", "entry level", "trainee", "apprentice"]},
    "mid": {"min_years": 2, "max_years": 5, "title_patterns": ["mid", "intermediate", "support engineer", "technical support"]},
    "senior": {"min_years": 5, "max_years": 10, "title_patterns": ["senior", "lead", "principal", "architect"]},
    "executive": {"min_years": 8, "max_years": 99, "title_patterns": ["director", "head of", "vp", "c-level", "cto", "cio"]},
}


def extract_job_skills(job: dict) -> dict[str, float]:
    """Extract skills from job listing with confidence scores."""
    text = " ".join([
        job.get("title", ""),
        job.get("company", ""),
        job.get("why", ""),
        job.get("description", ""),
        " ".join(job.get("tags", [])),
    ]).lower()

    found_skills = {}
    for skill_name, skill_info in SKILL_DB.items():
        for alias in skill_info["aliases"]:
            if alias in text:
                confidence = 0.5
                if alias in job.get("title", "").lower():
                    confidence = 1.0
                elif alias in " ".join(job.get("tags", [])):
                    confidence = 0.9
                elif alias in job.get("why", "").lower():
                    confidence = 0.8
                elif alias in job.get("description", "").lower():
                    confidence = 0.7
                else:
                    confidence = 0.6
                found_skills[skill_name] = max(found_skills.get(skill_name, 0), confidence)
                break
    return found_skills


def determine_experience_level(job: dict) -> str:
    """Determine required experience level from job title/description."""
    text = " ".join([
        job.get("title", ""),
        job.get("description", ""),
        job.get("why", ""),
    ]).lower()

    for level, info in EXPERIENCE_LEVELS.items():
        for pattern in info["title_patterns"]:
            if pattern in text:
                return level
    return "mid"


def calculate_skill_match(job_skills: dict[str, float], profile: dict) -> tuple[float, list[str], list[str]]:
    """Calculate skill match score. Returns: (score, matched_skills, missing_skills)"""
    matched = []
    missing = []
    total_weight = 0
    matched_weight = 0

    for skill_name, confidence in job_skills.items():
        skill_info = SKILL_DB.get(skill_name)
        if not skill_info:
            continue
        weight = {"expert": 1.0, "advanced": 0.8, "intermediate": 0.6, "basic": 0.4}.get(skill_info["level"], 0.5)
        total_weight += weight
        if confidence >= 0.6:
            matched.append(skill_name)
            matched_weight += weight * confidence
        else:
            missing.append(skill_name)

    if total_weight == 0:
        return 0.5, matched, missing
    score = min(1.0, matched_weight / total_weight)
    return score, matched, missing


def calculate_experience_fit(job: dict, profile: dict) -> float:
    """Calculate how well Sam's experience matches the role level."""
    level = determine_experience_level(job)
    level_info = EXPERIENCE_LEVELS[level]
    sam_years = 6

    if level == "junior":
        return 0.7
    elif level == "mid":
        if level_info["min_years"] <= sam_years <= level_info["max_years"]:
            return 1.0
        elif sam_years < level_info["min_years"]:
            return 0.6
        else:
            return 0.8
    elif level == "senior":
        if sam_years >= level_info["min_years"]:
            return 0.9
        else:
            return max(0.5, 0.9 - (level_info["min_years"] - sam_years) * 0.1)
    elif level == "executive":
        return 0.3
    return 0.5


def calculate_location_fit(job: dict) -> float:
    """Calculate location/remote fit."""
    location = job.get("location", "").lower()
    remote = job.get("remote", False)

    if remote:
        return 1.0
    if "melbourne" in location or "vic" in location:
        return 0.9
    elif "sydney" in location or "nsw" in location:
        return 0.6
    elif "brisbane" in location or "qld" in location:
        return 0.5
    elif "perth" in location or "wa" in location:
        return 0.4
    elif "remote" in location or "work from home" in location:
        return 1.0
    else:
        return 0.5


def calculate_company_fit(job: dict) -> float:
    """Calculate company size/type fit."""
    company = job.get("company", "").lower()
    title = job.get("title", "").lower()
    tags = " ".join(job.get("tags", [])).lower()
    text = f"{company} {title} {tags}"

    if any(word in text for word in ["government", "victorian", "victoria", "department of", "council", "public sector"]):
        return 0.95
    if any(word in text for word in ["bank", "university", "hospital", "health", "aws", "microsoft", "google", "amazon"]):
        return 0.9
    if any(word in text for word in ["consulting", "managed services", "msp", "solutions"]):
        return 0.85
    if any(word in text for word in ["technology", "tech", "digital", "cloud", "software"]):
        return 0.8
    return 0.7


def calculate_growth_potential(job: dict) -> float:
    """Calculate growth/learning potential."""
    title = job.get("title", "").lower()
    tags = " ".join(job.get("tags", [])).lower()
    text = f"{title} {tags}"

    if any(word in text for word in ["trainee", "apprentice", "training", "graduate", "junior"]):
        return 0.9
    if any(word in text for word in ["cloud", "azure", "devops", "kubernetes", "terraform"]):
        return 0.8
    if any(word in text for word in ["lead", "senior", "principal", "architect"]):
        return 0.7
    return 0.5


def score_job(job: dict) -> dict:
    """Multi-dimensional job scoring engine. Returns comprehensive fit analysis."""
    profile = load_profile()

    job_skills = extract_job_skills(job)
    skill_score, matched_skills, missing_skills = calculate_skill_match(job_skills, profile)
    experience_fit = calculate_experience_fit(job, profile)
    location_fit = calculate_location_fit(job)
    company_fit = calculate_company_fit(job)
    growth_potential = calculate_growth_potential(job)

    weights = {
        "skill_match": 0.40,
        "experience_fit": 0.25,
        "location_fit": 0.15,
        "company_fit": 0.10,
        "growth_potential": 0.10,
    }

    total_score = (
        skill_score * weights["skill_match"] +
        experience_fit * weights["experience_fit"] +
        location_fit * weights["location_fit"] +
        company_fit * weights["company_fit"] +
        growth_potential * weights["growth_potential"]
    )

    confidence = 0.5
    if job.get("description"):
        confidence += 0.2
    if job.get("tags"):
        confidence += 0.1
    if job.get("why"):
        confidence += 0.1
    if len(job_skills) > 3:
        confidence += 0.1
    confidence = min(1.0, confidence)

    # Strengths and risks
    strengths = []
    if matched_skills:
        strengths.append(f"Strong skill alignment in {', '.join(matched_skills[:3])}")
    if experience_fit >= 0.8:
        strengths.append("Experience level matches role requirements")
    if location_fit >= 0.9:
        strengths.append("Ideal location match (Melbourne-based)")
    strengths.append("Proven track record in enterprise environments")

    risks = []
    if missing_skills:
        risks.append(f"Missing skills: {', '.join(missing_skills[:3])}")
    if experience_fit < 0.5:
        risks.append("Experience level below role requirements")
    if len(missing_skills) > 3:
        risks.append("Multiple skill gaps may require significant upskilling")
    risks.append("Verify exact requirements before applying")

    if total_score >= 0.85:
        fit_category = "Excellent fit"
    elif total_score >= 0.70:
        fit_category = "Strong fit"
    elif total_score >= 0.55:
        fit_category = "Good fit"
    elif total_score >= 0.40:
        fit_category = "Partial fit"
    else:
        fit_category = "Weak fit"

    return {
        "score": round(total_score * 100),
        "fit": fit_category,
        "dimensions": {
            "skill_match": round(skill_score * 100),
            "experience_fit": round(experience_fit * 100),
            "location_fit": round(location_fit * 100),
            "company_fit": round(company_fit * 100),
            "growth_potential": round(growth_potential * 100),
        },
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "strengths": strengths[:3],
        "risks": risks[:3],
        "confidence": round(confidence, 2),
        "experience_level": determine_experience_level(job),
        "job_skills_found": list(job_skills.keys()),
    }


# ─── Resume Generation ───────────────────────────────────────────────────────

def generate_tailored_summary(job: dict, audit: dict, category: str) -> str:
    """Generate a job-specific professional summary."""
    title = job.get("title", "").lower()
    matched = audit.get("matched_skills", [])
    company = job.get("company", "the organisation")

    if any(w in title for w in ["cloud", "azure", "m365", "sharepoint"]):
        return f"Cloud and Microsoft 365 engineer with {len(matched)+3}+ years of hands-on experience in {', '.join(matched[:3])}. Proven track record managing enterprise environments at scale, from migration and deployment through to automation and Tier-3 support."
    elif any(w in title for w in ["support", "service desk", "help desk"]):
        return f"Technical support professional with {len(matched)+2}+ years of enterprise experience in {', '.join(matched[:3])}. Known for rapid issue resolution, clear communication, and building automation that eliminates recurring toil."
    elif any(w in title for w in ["infrastructure", "devops", "platform"]):
        return f"Infrastructure engineer with {len(matched)+3}+ years of experience across {', '.join(matched[:3])}. Combines hands-on technical execution with automation-first thinking to deliver reliable, scalable infrastructure."
    elif any(w in title for w in ["trainee", "apprentice", "junior"]):
        return f"Motivated professional with practical experience in {', '.join(matched[:3])}. Eager to develop new skills through structured training and supervised work in a technical environment."
    elif any(w in title for w in ["casual", "warehouse", "hospitality", "retail"]):
        return f"Melbourne-based professional seeking a practical local role. Brings dependable service operations, {', '.join(matched[:3])}, and the ability to learn new procedures quickly."
    else:
        return f"Infrastructure and Microsoft 365 engineer with {len(matched)+3}+ years of progressive experience across {', '.join(matched[:3])}. Trusted for Tier-3 escalations, enterprise automation, and delivering durable outcomes."


def generate_tailored_skills_section(job: dict, audit: dict) -> str:
    """Generate skills section ordered by job relevance."""
    matched = audit.get("matched_skills", [])
    complementary = ["powershell", "windows", "servicenow", "itil", "customer service", "documentation"]
    skills = list(matched)
    for skill in complementary:
        if skill not in skills:
            skills.append(skill)
    return " · ".join(skills[:12])


def reorder_experience_sections(job: dict, audit: dict, category: str, entries: list) -> list[dict]:
    """Reorder experience sections based on job relevance."""
    job_text = " ".join([
        job.get("title", ""),
        job.get("why", ""),
        " ".join(job.get("tags", [])),
    ]).lower()

    scored = []
    for entry in entries:
        score = entry.get("relevance_weights", {}).get(category, 0.5)
        heading = entry.get("heading", "").lower()
        skills_used = " ".join(entry.get("skills_used", [])).lower()

        for skill in audit.get("matched_skills", []):
            if skill in skills_used:
                score += 0.3
            if skill in heading:
                score += 0.5

        scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored]


def reorder_bullets(bullets: list[str], job: dict, audit: dict) -> list[str]:
    """Reorder bullets within a section based on job relevance."""
    job_text = " ".join([
        job.get("title", ""),
        job.get("why", ""),
        " ".join(job.get("tags", [])),
    ]).lower()

    scored = []
    for bullet in bullets:
        score = 0
        bullet_lower = bullet.lower()
        for skill in audit.get("matched_skills", []):
            if skill in bullet_lower:
                score += 1
        if re.search(r'\d+%', bullet) or re.search(r'\d+ (hour|month|year|user|site|endpoint)', bullet):
            score += 1
        action_verbs = ["built", "engineered", "led", "managed", "delivered", "automated", "implemented", "designed"]
        if any(verb in bullet_lower for verb in action_verbs):
            score += 1
        scored.append((score, bullet))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [bullet for _, bullet in scored]


def generate_tailored_resume(job: dict, audit: dict, category: str) -> str:
    """Generate a fully tailored resume for this specific job."""
    # Import entries from the main module
    try:
        from generate_all_application_materials import (
            EXPERIENCE_ENTRIES,
            PROJECTS_BY_CATEGORY,
        )
    except ImportError:
        from generate_all_application_materials import EXPERIENCE_ENTRIES
        PROJECTS_BY_CATEGORY = {}

    title = job.get("title", "Target Role")
    summary = generate_tailored_summary(job, audit, category)
    skills = generate_tailored_skills_section(job, audit)
    experience = reorder_experience_sections(job, audit, category, EXPERIENCE_ENTRIES)
    projects = PROJECTS_BY_CATEGORY.get(category, [])

    lines = [
        "# Sam Ludwig",
        "Melbourne, VIC | 0405 993 245 | sam.ludwig@gmail.com",
        "samludwig.au | github.com/Ludwixix",
        "",
        f"## Target Role: {title}",
        "",
        "### Professional Summary",
        summary,
        "",
        "### Core Skills",
        skills,
        "",
        "### Professional Experience",
    ]

    for section in experience:
        lines.append(f"### {section['heading']}")
        lines.append(f"{section['period']} · {section.get('location', 'Melbourne')}")
        bullets = section.get("bullets_by_category", {}).get(category, section.get("bullets", []))
        reordered = reorder_bullets(bullets, job, audit)
        for bullet in reordered:
            lines.append(f"- {bullet}")
        lines.append("")

    if projects:
        lines.append("### Selected Projects")
        for project in projects[:3]:
            lines.append(f"- {project}")
        lines.append("")

    lines.extend([
        "### Qualifications",
        "AZ-104 Azure Administrator Associate · AZ-900 Azure Fundamentals · ITIL 4 Foundation · Certified Scrum Master · Diploma of Information Technology — Coder Academy",
        "",
        "### Work Rights",
        "Australian citizen · unrestricted Australian work rights · available immediately",
    ])

    return "\n".join(lines)


# ─── Cover Letter Generation ─────────────────────────────────────────────────

def generate_company_hook(job: dict) -> str:
    """Generate a company-specific hook for the cover letter."""
    company = job.get("company", "").lower()
    title = job.get("title", "").lower()

    if any(w in company for w in ["government", "victorian", "council", "department"]):
        return f"I'm drawn to {job.get('company', 'this organisation')} because of the opportunity to contribute to public service delivery at scale."
    if any(w in company for w in ["health", "hospital", "medical", "clinical"]):
        return "I understand the critical importance of reliable technology in healthcare environments, where system uptime directly impacts patient care."
    if any(w in company for w in ["education", "university", "school", "college"]):
        return "I'm excited about supporting educational technology that enables learning outcomes for students and educators."
    if any(w in title for w in ["cloud", "azure", "m365", "sharepoint"]):
        return "I'm passionate about cloud technology and its potential to transform how organisations operate."
    if any(w in title for w in ["support", "service desk", "help desk"]):
        return "I enjoy the direct impact of technical support — solving problems that help people do their jobs more effectively."
    if any(w in title for w in ["casual", "warehouse", "hospitality", "retail"]):
        return "I'm looking for a practical local role where I can contribute reliably and learn new procedures."
    return "I'm interested in this role because it aligns with my experience in enterprise technology."


def quantify_achievement_for_role(audit: dict) -> str:
    """Select and quantify the most relevant achievement for this role."""
    matched = audit.get("matched_skills", [])

    achievements = {
        "azure": "At Capgemini, I led Azure cloud adoption initiatives aligned with ACSC Essential 8 security baselines, managing legacy application remediation and infrastructure modernisation.",
        "sharepoint": "I managed the largest SharePoint farm in the Southern Hemisphere with 660,000+ users and 1,000+ site collections, maintaining 99.9% uptime across government environments.",
        "powershell": "I engineered PnP PowerShell automation that replaced a month-long manual audit cycle, auditing and enforcing MFA compliance across 200+ sensitive SharePoint sites.",
        "intune": "At St John of God Health Care, I led Windows 11 migration across 100+ clinical endpoints using Autopilot and Intune, with 100% enrolment adherence in a live hospital environment.",
        "servicenow": "I built ServiceNow automation that eliminated hundreds of hours of repetitive manual data entry each month while working within locked-down endpoint controls.",
        "exchange": "I administered Exchange Hybrid and Online environments, resolving complex mail-flow, calendar, and federation issues for enterprise users.",
        "windows": "I managed endpoint lifecycle across multiple organisations, including hardware preparation, Autopilot enrolment, Intune policy application, and post-deployment validation.",
        "customer service": "I delivered L1-L3 technical support within SLA, building automation that reduced resolution time and improved team onboarding.",
    }

    for skill in matched:
        if skill in achievements:
            return achievements[skill]

    return "At Australia Post via Capgemini, I delivered hardware diagnostics, Windows imaging, endpoint provisioning, Autopilot/UEM enrolment, inventory control, loan-device management and compliant disposal within strict operational parameters."


def generate_tailored_cover_letter(job: dict, audit: dict, category: str) -> str:
    """Generate a tailored cover letter for this specific job."""
    title = job.get("title", "the position")
    company = job.get("company", "your organisation")
    matched = audit.get("matched_skills", [])

    company_hook = generate_company_hook(job)
    achievement = quantify_achievement_for_role(audit)
    skills_mention = ", ".join(matched[:3]) if matched else "enterprise technology"

    paragraphs = [
        "Dear Hiring Manager,",
        "",
        f"I'm applying for the {title} position with {company}. {company_hook}",
        "",
        f"{achievement}",
        "",
        f"The areas most relevant to this role are {skills_mention}. I'd bring dependable task ownership, clear communication, and a willingness to learn how your team works.",
        "",
        "I'm happy to confirm any licence, qualification, check, vehicle, roster or prior-industry requirements before progressing.",
        "",
        "Thank you for considering my application. I would welcome a conversation about how my background could contribute to your team.",
        "",
        "Yours sincerely,",
        "Sam Ludwig",
    ]

    return "\n".join(paragraphs)


def generate_tailored_email(job: dict, audit: dict, category: str) -> str:
    """Generate a tailored opening email for this specific job."""
    title = job.get("title", "the position")
    company = job.get("company", "your organisation")
    location = job.get("location", "Melbourne")
    url = job.get("url", "")
    matched = audit.get("matched_skills", [])
    skills_mention = ", ".join(matched[:3]) if matched else "enterprise technology"

    lines = [
        f"# Opening Email — {title}",
        "",
        f"**Company:** {company}",
        f"**Location:** {location}",
        f"**Application link:** {url}",
        "",
        "## Subject",
        f"Application — {title} — Sam Ludwig",
        "",
        "## Email body",
        "Hello Hiring Manager,",
        "",
        f"I'm writing about the {title} position with {company}. I believe my experience aligns well with the role requirements.",
        "",
        "My background includes enterprise technical support, endpoint lifecycle management, and process-focused documentation.",
        "",
        f"The areas most relevant to the role are {skills_mention}. I'd welcome a brief conversation about the role and any position-specific requirements.",
        "",
        "Regards,",
        "Sam Ludwig",
        "0405 993 245",
        "sam.ludwig@gmail.com",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    test_job = {
        "title": "Senior Cloud Engineer",
        "company": "Victorian Institute of Teaching",
        "location": "Melbourne, VIC",
        "why": "Azure cloud engineering role with M365 and Entra ID",
        "tags": ["azure", "m365", "cloud", "government"],
        "description": "Senior cloud engineer with Azure, Intune, and enterprise experience",
        "remote": False,
    }

    result = score_job(test_job)
    print(json.dumps(result, indent=2))
