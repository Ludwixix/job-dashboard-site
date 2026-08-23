#!/usr/bin/env python3
"""Reclassify jobs into the correct IT subcategories.

Reads jobs_nonlinkedin_2026-08-08.json and adds a 'subcategory' field
to each job based on title, tags, and why-field keyword analysis.

Also identifies non-IT jobs that should be in technician/outdoor/local sections.
"""
import json
import re
import sys
from pathlib import Path

# ── Classification rules ──────────────────────────────────────────────────
# Each rule: (subcategory_id, keywords_in_title, keywords_in_tags, min_score)
# Title matches are weighted 3x, tag matches 1x.

CATEGORIES = {
    "cloud-devops": {
        "title": [
            "cloud", "devops", "dev-ops", "sre", "site reliability",
            "platform engineer", "infrastructure automation", "kubernetes",
            "docker", "terraform", "ci/cd", "cicd", "azure", "aws",
            "gcp", "cloud engineer", "cloud operations", "cloud infrastructure",
        ],
        "tags": [
            "azure", "aws", "gcp", "cloud", "devops", "kubernetes", "docker",
            "terraform", "ci/cd", "infrastructure automation", "containerisation",
            "cloud platforms",
        ],
    },
    "security": {
        "title": [
            "cyber security", "cybersecurity", "security engineer",
            "security architect", "soc analyst",
            "penetration test", "vulnerability", "security operations",
            "infosec", "information security", "ciso", "security manager",
            "security consultant", "security testing",
            "cyber risk", "insider risk", "digital forensic",
            "incident response", "forensic investigator",
            "risk assessor", "grc engineer", "grc analyst",
        ],
        "tags": [
            "cyber security", "soc", "vulnerability",
            "penetration testing", "iso 27001",
            "essential eight", "security controls",
        ],
    },
    "m365-identity": {
        "title": [
            "m365", "microsoft 365", "office 365", "o365", "enta",
            "intune", "mdm", "endpoint manager",
            "access management", "euc", "end user computing",
            "modern workplace", "workplace engineer",
        ],
        "tags": [
            "microsoft 365", "m365", "enta", "intune", "mdm",
            "identity and access management", "end-user computing",
            "endpoint", "modern workplace", "conditional access",
        ],
    },
    "service-desk": {
        "title": [
            "service desk", "help desk", "helpdesk", "desktop support",
            "it support", "technical support", "support engineer",
            "support technician", "l1", "l2", "l3", "level 1",
            "level 2", "level 3", "first line", "second line",
            "desktop & network support", "emr help desk",
            "it operations technician", "operations technician",
            "support officer", "it officer",
        ],
        "tags": [
            "service desk", "help desk", "desktop support", "it support",
            "technical support", "l1 support", "l2 support",
        ],
    },
    "infrastructure-systems": {
        "title": [
            "systems administrator", "sysadmin", "network engineer",
            "network administrator", "infrastructure engineer",
            "server administrator", "data centre", "datacenter",
            "storage engineer", "backup engineer", "virtualisation",
            "vmware", "windows server", "linux administrator",
            "infrastructure", "systems engineer",
            "principal architect.*telecom",
            "system administrator", "systems admin",
            "network planning", "systems modelling",
            "technical operations manager",
        ],
        "tags": [
            "windows server", "linux", "vmware", "networking",
            "infrastructure", "servers", "data centre", "storage",
            "backup", "virtualisation", "active directory",
        ],
    },
    "software-data": {
        "title": [
            "software engineer", "software developer", "developer",
            "data engineer", "data scientist", "machine learning",
            "ai engineer", "full stack", "full-stack", "backend",
            "frontend", "frontend", "dev", "programmer",
            "cyber identity engineer", "digital solutions specialist",
            "microsoft business applications",
            "solutions architect",
        ],
        "tags": [
            "software", "python", "java", "javascript", "typescript",
            "data engineering", "machine learning", "ai", "api",
            "microservices", "database",
        ],
    },
    "project-management": {
        "title": [
            "project manager", "program manager", "delivery manager",
            "business analyst", "product manager", "scrum master",
            "agile", "it manager", "service manager", "change manager",
            "release manager", "delivery practice analyst",
            "director.*service delivery", "jira admin",
            "finance analyst", "risk.*analyst", "market analyst",
            "forecast analyst", "product improvement analyst",
            "strategy consultant", "financial analyst",
            "account executive", "compliance officer",
            "investment compliance", "governance analyst",
            "hcm lead", "technical account manager",
            "vendor manager", "strategy & consulting",
            "advisory technology", "director",
            "head of.*enablement",
        ],
        "tags": [
            "project management", "agile", "scrum", "business analysis",
            "service delivery", "change management", "stakeholder",
            "vendor management", "sla",
        ],
    },
}

# Non-IT job indicators — these should NOT be in any IT subcategory
NON_IT_TITLE_KEYWORDS = [
    "gardener", "grounds", "landscaping", "mowing", "brushcutting",
    "housekeeper", "cleaner", "barista", "bartender", "chef", "cook",
    "retail", "sales assistant", "merchandiser", "cashier",
    "panel beater", "spray painter", "apprentice technician",
    "ranger", "recreation", "sports team",
    "heritage", "cultural values officer",
    "food & beverage", "waiter", "kitchen",
    "forklift",
    "nurse", "triage nurse",
    "receptionist",
    "policy adviser", "policy officer",
    "warehouse administrator", "warehouse assistant",
    "biomedical engineer",
    "casual teacher",
    "customer engineer.*thermal",
    "thermal engineer",
    "legal assistant", "insurance litigation",
    "underwriter", "corporate property",
    "talent acquisition", "recruitment",
    "communications officer", "outreach officer",
    "field service technician",
    "real estate", "property manager",
    "events coordinator", "marketing coordinator",
    "public relations", "brand manager",
    "human resources", "hr manager",
    "payroll officer", "accounts payable",
    "bookkeeper", "financial planner",
    "insurance broker", "real estate agent",
    "sleep scientist", "quality officer",
    "relief and recovery officer",
    "strategy advisor", "strategy adviser",
    "inspector", "plumbing",
    "people experience partner",
    "people strategy",
    "administration assistant",
    "senior administration",
    "principal adviser",
    "senior project officer",
    "project officer",
    "sales & operations",
    "manager, support & delivery",
    "professional services consultant",
    "audit & assurance",
    "contracts manager",
    "hr assist",
    "office manager",
    "executive support",
    "people and learning",
    "payroll manager",
    "personal assistant",
    "ea to the ceo",
    "head of quality",
    "facilities officer",
    "business services administrator",
    "senior specialist, people",
    "contracts manager",
]


def classify_job(job: dict) -> str:
    """Classify a job into a subcategory based on title and tags."""
    title = (job.get("title") or "").lower()
    tags = [t.lower() for t in (job.get("tags") or [])]
    why = (job.get("why") or "").lower()

    # Check for non-IT first
    for kw in NON_IT_TITLE_KEYWORDS:
        if re.search(kw, title):
            return "non-it"

    # Priority overrides: certain title keywords are definitive
    # Project management roles win if title matches strongly
    pm_title_kw = ["project manager", "program manager", "delivery manager",
                    "business analyst", "scrum master"]
    for kw in pm_title_kw:
        if re.search(kw, title):
            return "project-management"

    # Software/data roles
    sw_title_kw = ["software engineer", "software developer", "quality engineer",
                    "data engineer", "full stack", "full-stack"]
    for kw in sw_title_kw:
        if re.search(kw, title):
            return "software-data"

    # Score each category
    scores = {}
    for cat_id, rules in CATEGORIES.items():
        score = 0
        # Title matches (weight 3)
        for kw in rules["title"]:
            if re.search(kw, title):
                score += 3
        # Tag matches (weight 1)
        for kw in rules["tags"]:
            for tag in tags:
                if kw in tag:
                    score += 1
        # Why-field bonus (weight 0.5)
        for kw in rules["title"] + rules["tags"]:
            if re.search(kw, why):
                score += 0.5
        if score > 0:
            scores[cat_id] = score

    if not scores:
        return "unclassified"

    return max(scores, key=scores.get)


def reclassify(data: dict) -> dict:
    """Add subcategory field to all jobs and return updated data."""
    jobs = data.get("jobs", [])

    stats = {"total": len(jobs), "categories": {}, "non-it": 0, "unclassified": 0}

    for job in jobs:
        subcat = classify_job(job)
        job["subcategory"] = subcat
        stats["categories"][subcat] = stats["categories"].get(subcat, 0) + 1
        if subcat == "non-it":
            stats["non-it"] += 1
        elif subcat == "unclassified":
            stats["unclassified"] += 1

    # Also classify section jobs
    for section_name, section_jobs in data.get("sections", {}).items():
        for job in section_jobs:
            if not job.get("subcategory"):
                job["subcategory"] = classify_job(job)

    return data, stats


def main():
    input_path = Path(__file__).parent / "jobs_nonlinkedin_2026-08-08.json"
    output_path = Path(__file__).parent / "jobs_nonlinkedin_2026-08-08_reclassified.json"

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    data, stats = reclassify(data)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Reclassified {stats['total']} jobs → {output_path.name}")
    print("\nCategory distribution:")
    for cat, count in sorted(stats["categories"].items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    print(f"\n  Non-IT (excluded from IT categories): {stats['non-it']}")
    print(f"  Unclassified (no strong match): {stats['unclassified']}")

    # Show some misclassified examples from original
    print("\nSample corrections (jobs that moved category):")
    for job in data["jobs"][:300]:
        title = job.get("title", "?")
        subcat = job.get("subcategory", "?")
        # Check if this looks wrong in the original HTML categories
        if subcat == "non-it":
            print(f"  ✓ MOVED OUT: {title} → non-it section")
        elif subcat == "unclassified":
            print(f"  ? UNCLEAR: {title} → needs review")


if __name__ == "__main__":
    main()
