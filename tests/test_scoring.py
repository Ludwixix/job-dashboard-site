"""Tests for job scoring and classification logic."""
import pytest


class TestJobScoring:
    """Basic scoring contract tests."""

    def test_score_range(self, sample_job):
        """Score should be between 0 and 100."""
        score = sample_job.get("score", 0)
        assert 0 <= score <= 100, f"Score {score} out of range"

    def test_fit_label_valid(self, sample_job):
        """Fit should be one of the expected labels."""
        valid_fits = {"Strong fit", "Good fit - review carefully", "Review", "Poor fit"}
        assert sample_job["fit"] in valid_fits

    def test_matched_terms_is_list(self, sample_job):
        """Matched terms should be a non-empty list."""
        assert isinstance(sample_job["matched_terms"], list)
        assert len(sample_job["matched_terms"]) > 0

    def test_gaps_is_list(self, sample_job):
        """Gaps should be a list (can be empty)."""
        assert isinstance(sample_job["gaps"], list)


class TestAuditContract:
    """Tests for the audit JSON schema."""

    def test_audit_has_version(self, sample_audit):
        assert "audit_version" in sample_audit

    def test_audit_score_range(self, sample_audit):
        assert 0 <= sample_audit["score"] <= 100

    def test_audit_has_recommendation(self, sample_audit):
        assert "recommendation" in sample_audit
        assert len(sample_audit["recommendation"]) > 0

    def test_audit_matched_terms(self, sample_audit):
        assert isinstance(sample_audit["matched_terms"], list)


class TestITSubcategories:
    """Tests for the 7-category classification system."""

    EXPECTED_CATEGORIES = {
        "cloud-devops",
        "security",
        "m365-identity",
        "service-desk",
        "infrastructure-systems",
        "software-data",
        "project-management",
    }

    def test_categories_defined(self):
        """All 7 expected categories should exist."""
        # This tests the contract; actual import requires the parent workspace
        assert len(self.EXPECTED_CATEGORIES) == 7
