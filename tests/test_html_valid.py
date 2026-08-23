"""Smoke tests for the generated dashboard HTML."""
import os


class TestIndexHTML:
    """Verify index.html is valid and contains expected structure."""

    def test_file_exists(self, repo_root):
        assert os.path.exists(os.path.join(repo_root, "index.html"))

    def test_is_html(self, index_html):
        lower = index_html.strip().lower()
        assert lower.startswith(("<!doctype html>", "<html"))

    def test_has_head(self, index_html):
        assert "<head" in index_html.lower()

    def test_has_body(self, index_html):
        assert "<body" in index_html.lower()

    def test_has_title(self, index_html):
        assert "<title" in index_html.lower()

    def test_has_responsive_meta(self, index_html):
        assert "viewport" in index_html.lower()

    def test_has_css(self, index_html):
        """Should contain embedded or linked styles."""
        assert "<style" in index_html.lower() or ".css" in index_html.lower()

    def test_has_js(self, index_html):
        """Should contain embedded or linked scripts."""
        assert "<script" in index_html.lower()

    def test_no_broken_links_in_css(self, index_html):
        """Basic check: no obviously broken URL references."""
        # Check for common mistakes
        assert 'src="undefined"' not in index_html
        assert "href=\"undefined\"" not in index_html

    def test_contains_job_cards(self, index_html):
        """Dashboard should render job cards."""
        assert "card" in index_html.lower()

    def test_contains_stage_controls(self, index_html):
        """Should have stage/status selection elements."""
        assert "stage" in index_html.lower() or "status" in index_html.lower()

    def test_file_size_reasonable(self, repo_root):
        """HTML shouldn't be suspiciously small (<1KB) or huge (>10MB)."""
        path = os.path.join(repo_root, "index.html")
        size = os.path.getsize(path)
        assert 1000 < size < 10_000_000, f"Unexpected HTML size: {size} bytes"
