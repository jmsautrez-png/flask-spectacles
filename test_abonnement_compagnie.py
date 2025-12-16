import unittest
import unicodedata
from app import create_app

class AbonnementCompagnieTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_abonnement_compagnie_route(self):
        response = self.client.get('/abonnement-compagnie')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        # Normalisation pour rendre le test robuste aux accents/variantes typographiques
        html_norm = unicodedata.normalize("NFKD", html).encode("ascii", "ignore").decode("ascii")
        # Remove apostrophes, quotes, and extra spaces for normalization
        html_norm = html_norm.replace("'", "").replace('"', '').replace("  ", " ")
        self.assertIn("SaaS dedie a la mise en relation", html_norm)
        self.assertIn("Abonnement mensuel", html_norm)
        self.assertIn("10", html_norm)  # Check price is present
        self.assertIn("Sabonner", html_norm)

if __name__ == "__main__":
    unittest.main()
