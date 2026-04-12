"""Tests for utility modules: utils.files, utils.security, utils.search, utils.seo."""
import pytest


class TestNormalizeSearchText:
    """Tests for utils.search.normalize_search_text."""

    def test_removes_accents(self):
        from utils.search import normalize_search_text
        assert "pere noel" == normalize_search_text("Père Noël")

    def test_lowercase(self):
        from utils.search import normalize_search_text
        assert normalize_search_text("SPECTACLE") == "spectacle"

    def test_removes_punctuation(self):
        from utils.search import normalize_search_text
        result = normalize_search_text("père-noël")
        assert "pere" in result and "noel" in result

    def test_normalizes_whitespace(self):
        from utils.search import normalize_search_text
        assert "a b" == normalize_search_text("  a   b  ")

    def test_empty_string(self):
        from utils.search import normalize_search_text
        assert "" == normalize_search_text("")

    def test_none_input(self):
        from utils.search import normalize_search_text
        assert "" == normalize_search_text(None)

    def test_apostrophe_handling(self):
        from utils.search import normalize_search_text
        result = normalize_search_text("l'école")
        assert "ecole" in result


class TestAllowedFile:
    """Tests for utils.files.allowed_file."""

    def test_valid_extensions(self):
        from utils.files import allowed_file
        for ext in ("png", "jpg", "jpeg", "gif", "webp", "pdf"):
            assert allowed_file(f"image.{ext}") is True

    def test_invalid_extension(self):
        from utils.files import allowed_file
        assert allowed_file("script.exe") is False
        assert allowed_file("page.html") is False
        assert allowed_file("data.csv") is False

    def test_no_extension(self):
        from utils.files import allowed_file
        assert allowed_file("noextension") is False

    def test_empty_filename(self):
        from utils.files import allowed_file
        assert allowed_file("") is False
        assert allowed_file(None) is False

    def test_case_insensitive(self):
        from utils.files import allowed_file
        assert allowed_file("photo.PNG") is True
        assert allowed_file("photo.JpG") is True


class TestOptimizeTitleSeo:
    """Tests for utils.seo.optimize_title_seo."""

    def test_returns_dict_with_required_keys(self):
        from utils.seo import optimize_title_seo
        result = optimize_title_seo("Spectacle de marionnettes")
        assert "original" in result
        assert "optimized" in result
        assert "suggestions" in result
        assert "seo_score" in result
        assert "improvements" in result

    def test_empty_title(self):
        from utils.seo import optimize_title_seo
        result = optimize_title_seo("")
        assert result["seo_score"] == 0

    def test_score_bounded(self):
        from utils.seo import optimize_title_seo
        result = optimize_title_seo("Spectacle de Marionnettes pour Enfants - Animation Professionnelle")
        assert 0 <= result["seo_score"] <= 100

    def test_short_title_penalized(self):
        from utils.seo import optimize_title_seo
        result = optimize_title_seo("Court")
        assert any("court" in imp.lower() for imp in result["improvements"])

    def test_suggestions_max_5(self):
        from utils.seo import optimize_title_seo
        result = optimize_title_seo("Spectacle", category="magie", location="Paris", age_range="6-10")
        assert len(result["suggestions"]) <= 5


class TestIsSuspiciousRequest:
    """Tests for utils.security.is_suspicious_request."""

    def test_sqlmap_detected(self, app):
        from utils.security import is_suspicious_request
        with app.test_request_context(headers={"User-Agent": "sqlmap/1.5"}):
            assert is_suspicious_request() is True

    def test_normal_browser(self, app):
        from utils.security import is_suspicious_request
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        with app.test_request_context(headers={"User-Agent": ua}):
            assert is_suspicious_request() is False

    def test_empty_user_agent(self, app):
        from utils.security import is_suspicious_request
        with app.test_request_context(headers={"User-Agent": ""}):
            assert is_suspicious_request() is True


class TestIsBotVisitor:
    """Tests for utils.security.is_bot_visitor."""

    def test_googlebot(self):
        from utils.security import is_bot_visitor
        assert is_bot_visitor("Googlebot/2.1") is True

    def test_normal_browser(self):
        from utils.security import is_bot_visitor
        assert is_bot_visitor("Mozilla/5.0 (Windows NT 10.0; Win64; x64)") is False

    def test_empty_user_agent(self):
        from utils.security import is_bot_visitor
        assert is_bot_visitor("") is False

    def test_selenium_detected(self):
        from utils.security import is_bot_visitor
        assert is_bot_visitor("Mozilla/5.0 selenium") is True

    def test_hosting_isp_flagged(self):
        from utils.security import is_bot_visitor
        result = is_bot_visitor("Mozilla/5.0", isp="Amazon Technologies Inc.")
        assert result is True

    def test_residential_isp_ok(self):
        from utils.security import is_bot_visitor
        result = is_bot_visitor("Mozilla/5.0", isp="Orange S.A.")
        assert result is False


class TestGeneratePassword:
    """Tests for utils.security.generate_password."""

    def test_default_length(self):
        from utils.security import generate_password
        pwd = generate_password()
        assert len(pwd) == 10

    def test_custom_length(self):
        from utils.security import generate_password
        pwd = generate_password(20)
        assert len(pwd) == 20

    def test_alphanumeric(self):
        from utils.security import generate_password
        pwd = generate_password(100)
        assert pwd.isalnum()

    def test_randomness(self):
        from utils.security import generate_password
        passwords = {generate_password() for _ in range(50)}
        assert len(passwords) > 45  # Very unlikely to have collisions


class TestSeoCategories:
    """Tests for SEO_CATEGORIES constant."""

    def test_categories_not_empty(self):
        from utils.seo import SEO_CATEGORIES
        assert len(SEO_CATEGORIES) > 10

    def test_key_categories_exist(self):
        from utils.seo import SEO_CATEGORIES
        for key in ("marionnette", "magie", "clown", "cirque", "enfant"):
            assert key in SEO_CATEGORIES
