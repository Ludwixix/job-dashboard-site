#!/usr/bin/env python3
"""
3-Stream Job Classifier for Sam's Job Dashboard.

Classifies jobs into three streams based on the Product Specification:
  1. Core IT & Systems Engineering
  2. Local "Bridge" & Casual Work
  3. Technical Traineeships & Trade Pathways

Usage:
  from stream_classifier import classify_job, classify_all_jobs
"""
import re
from typing import Literal

StreamType = Literal["core-it", "bridge", "traineeship"]


# ── Stream definitions with keyword patterns ──────────────────────────────

STREAM_1_CORE_IT = {
    "id": "core-it",
    "name": "Core IT & Systems Engineering",
    "icon": "💻",
    "color": "#62d9ff",
    "desc": "Mid-level enterprise IT infrastructure, cloud platforms, identity administration, and technical support.",
    "objective": "Secure the primary next career step with compensation and responsibility matching mid-level systems engineering experience.",
    # Primary keywords (strong signal)
    "primary_keywords": [
        r"system.?admin",
        r"network.?engineer",
        r"cloud.?engineer",
        r"devops",
        r"cyber.?security",
        r"software.?engineer",
        r"data.?engineer",
        r"infrastructure.?engineer",
        r"platform.?engineer",
        r"azure",
        r"windows.?server",
        r"kubernetes",
        r"terraform",
        r"microsoft.?365",
        r"m365",
        r"enta.?id",
        r"intune",
        r"microsoft.?endpoint",
        r"euc",
        r"endpoint.?engineer",
        r"desktop.?support",
        r"it.?support",
        r"service.?desk",
        r"help.?desk",
        r"systems?.?engineer",
        r"linux.?admin",
        r"vmware",
        r"office.?365",
        r"microsoft.?defender",
        r"powershell",
        r"active.?directory",
        r"sql.?server",
        r"citrix",
        r"exchange.?server",
        r"sccm",
        r"mecm",
        r"macos.?admin",
        r"jira",
        r"servicenow",
        r"itil",
        r"sdwan",
        r"fortinet",
        r"cisco",
        r"palo.?alto",
        r"aws",
        r"gcp",
        r"google.?cloud",
        r"devsecops",
        r"sre",
        r"site.?reliability",
        r"monitoring",
        r"dynatrace",
        r"splunk",
        r"siem",
        r"security.?operations",
        r"soc.?analyst",
        r"penetration.?test",
        r"vulnerability",
        r"governance",
        r"risk",
        r"compliance",
        r"iso.?27001",
        r"nist",
        r"it.?project.?manager",
        r"it.?manager",
        r"technical.?lead",
        r"solution.?architect",
        r"database.?admin",
        r"data.?analyst",
        r"bi.?analyst",
        r"machine.?learning",
        r"ai.?engineer",
        r"full.?stack",
        r"backend.?developer",
        r"frontend.?developer",
        r"web.?developer",
        r"python.?developer",
        r"java.?developer",
        r"automation.?engineer",
        r"test.?engineer",
        r"qa.?engineer",
        r"quality.?assurance",
        r"scrum.?master",
        r"product.?owner",
        r"business.?analyst",
        r"it.?consultant",
        r"technical.?consultant",
    ],
    # Secondary keywords (weaker signal, need context)
    "secondary_keywords": [
        r"engineer",
        r"developer",
        r"analyst",
        r"architect",
        r"administrator",
        r"support",
        r"technician",
        r"consultant",
        r"lead",
        r"manager",
        r"specialist",
    ],
    # Exclusion keywords (if matched strongly, not core IT)
    "exclude_keywords": [
        r"barista",
        r"waiter",
        r"waitress",
        r"chef",
        r"cook",
        r"cleaner",
        r"gardener",
        r"landscap",
        r"warehouse.?hand",
        r"forklift",
        r"delivery.?driver",
        r"courier",
        r"retail.?assistant",
        r"sales.?assistant",
        r"cashier",
        r"housekeep",
        r"laundry",
        r"carpenter",
        r"plumber",
        r"electrician",
        r"hvac",
        r"bricklayer",
        r"concreter",
        r"painter",
        r"tiler",
        r"roofer",
        r"glazier",
        r"apprentice",
        r"traineeship",
        r"cabling",
        r"fibre",
        r"splice",
        r"data.?centre.?tech",
        r"racking",
        r"cage.?build",
        r"physical.?security",
        r"patrol",
        r"guard",
        r"receptionist",
        r"medical.?reception",
        r"admin.?assistant",
        r"office.?admin",
        r"accounts.?payable",
        r"payroll",
    ],
}

STREAM_2_BRIDGE = {
    "id": "bridge",
    "name": "Local \"Bridge\" & Casual Work",
    "icon": "🌉",
    "color": "#ffc857",
    "desc": "Immediate, low-barrier local employment. Casual/part-time roles within St Kilda, Balaclava, and inner Melbourne.",
    "objective": "Provide reliable casual or part-time income with scheduling flexibility while conducting the primary IT search.",
    # Strong signal: these in TITLE strongly indicate bridge work
    "title_keywords": [
        r"barista",
        r"waiter",
        r"waitress",
        r"bartender",
        r"kitchen.?hand",
        r"dishwasher",
        r"chef",
        r"cook",
        r"cleaner",
        r"cleaning",
        r"housekeep",
        r"laundry",
        r"ironer",
        r"presser",
        r"gardener",
        r"gardening",
        r"landscap",
        r"labourer",
        r"general.?hand",
        r"handyman",
        r"picker",
        r"packer",
        r"forklift",
        r"warehouse.?hand",
        r"warehouse.?worker",
        r"night.?fill",
        r"shelf.?stacker",
        r"stock.?control",
        r"cashier",
        r"checkout",
        r"retail.?assistant",
        r"retail.?worker",
        r"retail.?team",
        r"retail.?sales",
        r"shop.?assistant",
        r"store.?assistant",
        r"sales.?assistant",
        r"courier",
        r"delivery.?driver",
        r"driver",
        r"car.?wash",
        r"detailer",
        r"pet.?groomer",
        r"dog.?walker",
        r"childcare",
        r"teacher.?aide",
        r"education.?assistant",
        r"playground.?supervisor",
        r"after.?school",
        r"vacation.?care",
        r"event.?staff",
        r"event.?set.?up",
        r"venue.?assistant",
        r"promotion.?staff",
        r"brand.?ambassador",
        r"merchandiser",
        r"mail.?room",
        r"post.?office",
        r"receiving",
        r"despatch",
        r"dispatch",
        r"food.?and.?beverage",
        r"bar.?staff",
        r"casual.?staff",
        r"casual.?role",
        r"casual.?position",
        r"part.?time.?role",
    ],
    "secondary_keywords": [
        r"casual",
        r"part.?time",
    ],
    # Exclusion: professional/office roles that aren't casual/bridge
    "exclude_keywords": [
        r"officer",
        r"adviser",
        r"advisor",
        r"manager",
        r"principal",
        r"senior",
        r"lead",
        r"director",
        r"executive",
        r"coordinator",
        r"strateg",
        r"policy",
        r"governance",
        r"compliance",
        r"audit",
        r"finance",
        r"account",
        r"legal",
        r"lawyer",
        r"solicitor",
        r"hr",
        r"human.?resource",
        r"recruitment",
        r"marketing",
        r"communications",
        r"public.?relations",
        r"journalist",
        r"editor",
        r"writer",
        r"content",
        r"social.?media",
        r"brand",
        r"campaign",
        r"fundrais",
        r"donor",
        r"volunteer",
        r"community",
        r"outreach",
        r"engagement",
        r"partnership",
        r"stakeholder",
        r"program",
        r"project",
        r"research",
        r"academic",
        r"lecturer",
        r"tutor",
        r"educator",
        r"teacher",
        r"nurse",
        r"doctor",
        r"physician",
        r"therapist",
        r"counsellor",
        r"psychologist",
        r"social.?work",
        r"patholog",
        r"scientist",
        r"lab",
        r"clinical",
        r"hospital",
        r"medical",
        r"health",
        r"patient",
    ],
    # Location boosters - if job is in these areas, boost bridge score
    "location_boosters": [
        r"st.?kilda",
        r"balaclava",
        r"prahran",
        r"st.?kilda.?east",
        r"st.?kilda.?road",
        r"melbourne.?3004",
        r"melbourne.?3005",
        r"melbourne.?3006",
        r"inner.?melbourne",
    ],
}

STREAM_3_TRAINEESHIP = {
    "id": "traineeship",
    "name": "Technical Traineeships & Trade Pathways",
    "icon": "🔧",
    "color": "#bda7ff",
    "desc": "Structured on-the-job training, apprenticeships, or employer-sponsored certifications.",
    "objective": "Expand career options into technical and hands-on trade disciplines with established learning pathways.",
    "primary_keywords": [
        r"traineeship",
        r"trainee",
        r"apprentice",
        r"apprenticeship",
        r"technician",
        r"cabling",
        r"fibre",
        r"splice",
        r"telecom",
        r"telecommunication",
        r"network.?cable",
        r"structured.?cabling",
        r"data.?centre",
        r"data.?center",
        r"racking",
        r"rack.?install",
        r"power.?distribution",
        r"hvac",
        r"air.?conditioning",
        r"refrigeration",
        r"mechanical.?services",
        r"plumber",
        r"plumbing",
        r"carpenter",
        r"carpentry",
        r"electrician",
        r"electrical",
        r"bricklayer",
        r"bricklaying",
        r"concreter",
        r"concreting",
        r"painter",
        r"painting",
        r"tiler",
        r"tiling",
        r"roofer",
        r"roofing",
        r"glazier",
        r"glazing",
        r"welder",
        r"welding",
        r"boilermaker",
        r"fabricat",
        r"metal.?fabricat",
        r"panel.?beater",
        r"spray.?painter",
        r"mechanic",
        r"motor.?mechanic",
        r"automotive",
        r"auto.?electrician",
        r"floor.?sander",
        r"flooring",
        r"landscaping",
        r"tree.?lopper",
        f"arborist",
        r"pest.?control",
        r"fire.?protection",
        r"fire.?sprinkler",
        r"solar.?installer",
        r"electric.?vehicle",
        r"ev.?charger",
        r"battery.?storage",
        r"nbn",
        r"fttp",
        r"fttn",
        r"fttc",
        r"hfc",
        r"fixed.?wireless",
        r"5g.?install",
        r"tower.?climb",
        r"antenna",
        r"satellite",
        r"cctv",
        r"alarm.?install",
        r"access.?control",
        r"intrusion",
        r"intercom",
        r"gate.?motor",
        r"door.?intercom",
        r"fire.?panel",
        r"emergency.?light",
        r"exit.?sign",
        r"switchboard",
        r"solar.?panel",
        r"battery.?install",
        r"ups.?install",
        r"generator",
        r"compressor",
        r"pump",
        r"valve",
        r"pipe.?fit",
        r"steam",
        r"boiler",
        r"chiller",
        r"cooling.?tower",
        r"air.?handling",
        r"bms",
        r"building.?management",
        r"commissioning",
        r"test.?and.?balance",
    ],
    "secondary_keywords": [
        r"trade",
        r"craft",
        r"skilled.?labour",
        r"hand.?tool",
        r"power.?tool",
    ],
}


def _text_match_score(text: str, patterns: list[str], weight: float = 1.0) -> float:
    """Count how many patterns match in the text, weighted."""
    if not text:
        return 0.0
    text_lower = text.lower()
    matches = sum(1 for p in patterns if re.search(p, text_lower))
    return matches * weight


def classify_job(job: dict) -> StreamType:
    """
    Classify a job into one of three streams.
    Returns: "core-it", "bridge", or "traineeship"
    """
    # Combine all searchable text
    title = job.get("title", "")
    company = job.get("company", "")
    description = job.get("description", "")
    tags = " ".join(job.get("tags", []))
    location = job.get("location", "")
    subcategory = job.get("subcategory", "")

    searchable = f"{title} {company} {description} {tags} {location}".lower()

    # ── Stream 3: Traineeships (check first - strongest signal) ──
    traineeship_score = 0.0
    traineeship_score += _text_match_score(title, STREAM_3_TRAINEESHIP["primary_keywords"], 3.0)
    traineeship_score += _text_match_score(searchable, STREAM_3_TRAINEESHIP["primary_keywords"], 1.0)
    traineeship_score += _text_match_score(title, STREAM_3_TRAINEESHIP["secondary_keywords"], 1.0)

    # ── Stream 2: Bridge / Casual ──
    bridge_score = 0.0
    bridge_score += _text_match_score(title, STREAM_2_BRIDGE["title_keywords"], 4.0)
    bridge_score += _text_match_score(searchable, STREAM_2_BRIDGE["title_keywords"], 1.0)
    bridge_score += _text_match_score(title, STREAM_2_BRIDGE["secondary_keywords"], 1.0)

    # Bridge exclusion: professional/office roles should not be bridge
    bridge_score -= _text_match_score(title, STREAM_2_BRIDGE.get("exclude_keywords", []), 3.0)

    # Location boost for bridge
    bridge_score += _text_match_score(location, STREAM_2_BRIDGE.get("location_boosters", []), 1.0)

    # Part-time/casual boost in title specifically
    if re.search(r"\b(casual|part.?time)\b", title.lower()):
        bridge_score += 3.0
    elif re.search(r"\b(casual|part.?time|contract|temporary|temp)\b", searchable):
        bridge_score += 1.5

    # ── Stream 1: Core IT ──
    core_it_score = 0.0
    core_it_score += _text_match_score(title, STREAM_1_CORE_IT["primary_keywords"], 3.0)
    core_it_score += _text_match_score(searchable, STREAM_1_CORE_IT["primary_keywords"], 1.0)
    core_it_score += _text_match_score(title, STREAM_1_CORE_IT["secondary_keywords"], 1.0)

    # Use existing subcategory as a hint
    if subcategory in ("cloud-devops", "security", "m365-identity", "service-desk",
                        "infrastructure-systems", "software-data", "project-management"):
        core_it_score += 5.0

    # Exclusion penalties for core IT
    core_it_score -= _text_match_score(searchable, STREAM_1_CORE_IT["exclude_keywords"], 3.0)

    # Bridge exclusion: penalize if title has strong IT signals
    it_title_signals = [r"engineer", r"developer", r"architect", r"admin", r"analyst",
                         r"manager", r"lead", r"consultant", r"cloud", r"devops",
                         r"security", r"cyber", r"software", r"data.?engineer",
                         r"infrastructure", r"platform", r"network", r"systems"]
    bridge_score -= _text_match_score(title, it_title_signals, 4.0)

    # ── Determine winner ──
    scores = {
        "core-it": core_it_score,
        "bridge": bridge_score,
        "traineeship": traineeship_score,
    }

    winner = max(scores, key=scores.get)

    # Minimum threshold: if all scores are very low, use heuristics
    if scores[winner] < 2.0:
        # Non-IT title signals: if title clearly indicates non-IT work, classify as bridge
        non_it_patterns = [
            r"officer", r"adviser", r"advisor",
            r"manager",
            r"consultant",
        ]
        # IT context words - if title has these alongside non-IT patterns, don't penalize
        it_context_words = ["IT", "tech", "system", "cloud", "network", "security",
                           "infrastructure", "platform", "project", "data", "digital"]
        title_lower = title.lower()
        has_non_it = any(re.search(p, title_lower) for p in non_it_patterns)
        # Check if there are IT context words that override the non-IT signal
        has_it_context = any(w.lower() in title_lower for w in it_context_words)
        if has_non_it and has_it_context:
            has_non_it = False  # IT context overrides non-IT pattern

        # Check for clear IT signals in title
        it_title_defaults = ["engineer", "developer", "admin", "support", "analyst",
                             "architect", "lead", "cloud", "devops", "security",
                             "cyber", "software", "data", "infrastructure", "platform",
                             "network", "systems", "service desk", "help desk", "IT"]
        has_it_title = any(w.lower() in title_lower for w in it_title_defaults)

        if has_it_title:
            return "core-it"
        elif has_non_it:
            # Non-IT, non-casual role: likely professional role, classify as core-it
            # unless it clearly matches bridge keywords
            if bridge_score > core_it_score and bridge_score > traineeship_score:
                return "bridge"
            return "core-it"
        else:
            # Ambiguous: default to core-it since Sam is primarily job-hunting for IT
            return "core-it"

    return winner


def classify_all_jobs(jobs: list[dict]) -> dict:
    """
    Classify all jobs and return organized by stream.
    Returns: {"core-it": [...], "bridge": [...], "traineeship": [...]}
    """
    streams = {"core-it": [], "bridge": [], "traineeship": []}

    for job in jobs:
        stream = classify_job(job)
        job["stream"] = stream
        streams[stream].append(job)

    return streams


# ── CLI test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json
    import sys

    # Test with sample jobs
    test_jobs = [
        {"title": "Cloud Engineer - Azure", "company": "Deloitte", "location": "Melbourne CBD", "description": "Looking for Azure cloud engineer with Kubernetes experience", "tags": ["cloud"]},
        {"title": "Barista - St Kilda", "company": "Cafe Latte", "location": "St Kilda, VIC", "description": "Casual barista needed", "tags": ["hospitality"]},
        {"title": "Apprentice Electrician", "company": "Sparky Services", "location": "Balaclava, VIC", "description": "Electrical apprenticeship available", "tags": ["trade"]},
        {"title": "Service Desk Analyst", "company": "ANZ Bank", "location": "Melbourne, VIC", "description": "L2 support for Windows and M365 environment", "tags": ["support"]},
        {"title": "Warehouse Worker - Night Shift", "company": "Woolworths", "location": "Dandenong, VIC", "description": "Casual warehouse picker/packer", "tags": ["warehouse"]},
        {"title": "Fibre Splicer - NBN", "company": "NBN Co", "location": "Melbourne, VIC", "description": "Fibre optic splicing for NBN rollout", "tags": ["telecom"]},
    ]

    print("Stream Classification Test\n" + "=" * 50)
    for job in test_jobs:
        stream = classify_job(job)
        info = {"core-it": STREAM_1_CORE_IT, "bridge": STREAM_2_BRIDGE, "traineeship": STREAM_3_TRAINEESHIP}[stream]
        print(f"\n  {info['icon']} [{stream.upper()}] {job['title']}")
        print(f"    Company: {job['company']} | Location: {job['location']}")
