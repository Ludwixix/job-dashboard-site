"""Shared test fixtures for job-dashboard-site."""
import os

import pytest


@pytest.fixture
def sample_job():
    """A minimal job record matching the dashboard schema."""
    return {
        "id": "test-001",
        "title": "Cloud Engineer",
        "company": "Acme Corp",
        "location": "Melbourne",
        "url": "https://example.com/job/001",
        "source": "Indeed",
        "score": 85,
        "fit": "Strong fit",
        "work_type": "Hybrid",
        "posted": "2026-08-20",
        "matched_terms": ["Azure", "Microsoft 365", "cloud infrastructure"],
        "gaps": [],
        "why": "Strong match for cloud and M365 skills.",
    }


@pytest.fixture
def sample_audit():
    """A minimal audit JSON record."""
    return {
        "audit_version": "1.0",
        "fit": "Strong fit",
        "score": 88,
        "source": "Indeed",
        "matched_terms": ["cloud operations", "Azure", "automation"],
        "unsupported_or_unverified_terms": [],
        "requirements_to_confirm": ["Confirm security clearance"],
        "recommendation": "Apply",
    }


@pytest.fixture
def repo_root():
    """Path to the repository root."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def index_html(repo_root):
    """Contents of the generated index.html."""
    path = os.path.join(repo_root, "index.html")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    pytest.skip("index.html not found — run build first")
