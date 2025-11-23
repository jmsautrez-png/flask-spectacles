import unittest
from app import create_app

class AbonnementCompagnieTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_abonnement_compagnie_route(self):
        response = self.client.get('/abonnement-compagnie')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        self.assertIn("Spectacle’ment Votre est un SaaS dédié à la mise en relation", html)
        self.assertIn("Abonnement mensuel (10 €/mois)", html)
        self.assertIn("Diffusion gratuite avec commission", html)

if __name__ == "__main__":
    unittest.main()
