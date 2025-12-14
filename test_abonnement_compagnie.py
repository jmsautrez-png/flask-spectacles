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
        self.assertIn("Spectaclement Vtre est un SaaS dedie a la mise en relation", html_norm)
        self.assertIn("Abonnement mensuel (10 /mois)", html_norm)
        self.assertIn("Sabonner", html_norm)

if __name__ == "__main__":
    unittest.main()
