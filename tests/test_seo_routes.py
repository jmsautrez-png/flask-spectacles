import unittest
from app import app, SEO_CATEGORIES, TOP_50_CITY_SLUGS

class TestSEORoutes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_seo_category_routes(self):
        for cat_slug in SEO_CATEGORIES.keys():
            url = f"/{cat_slug}/"
            resp = self.client.get(url, follow_redirects=False)
            self.assertIn(resp.status_code, [301, 302], f"{url} should redirect (got {resp.status_code})")

    def test_seo_category_city_routes(self):
        for cat_slug in SEO_CATEGORIES.keys():
            for city_slug in TOP_50_CITY_SLUGS:
                url = f"/{cat_slug}/{city_slug}/"
                resp = self.client.get(url, follow_redirects=False)
                self.assertIn(resp.status_code, [301, 302], f"{url} should redirect (got {resp.status_code})")

if __name__ == "__main__":
    unittest.main()
