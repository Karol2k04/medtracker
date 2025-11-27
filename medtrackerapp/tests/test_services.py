from unittest.mock import patch
from django.test import TestCase
from medtrackerapp.models import Medication

class DrugInfoMockTests(TestCase):
    """
    Testy dla metody fetch_external_info w modelu Medication.
    Mockują wywołanie zewnętrznego API, aby nie polegać na sieci.
    """

    @patch("medtrackerapp.services.requests.get")
    def test_fetch_external_info_success(self, mock_get):
        """
        Test pozytywny: API zwraca dane poprawnie.
        """
        # Mock odpowiedzi API w formacie, jaki zwraca metoda
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "name": "Aspirin",
            "manufacturer": "Unknown",
            "warnings": ["No warnings available"],
            "purpose": ["Not specified"]
        }

        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=1)
        data = med.fetch_external_info()

        # Sprawdzenie, czy dane zostały zwrócone
        self.assertIn("name", data)
        self.assertEqual(data["name"], "Aspirin")
        self.assertIn("manufacturer", data)
        self.assertIn("warnings", data)
        self.assertIn("purpose", data)

    @patch("medtrackerapp.services.requests.get")
    def test_fetch_external_info_error(self, mock_get):
        """
        Test negatywny: API rzuca wyjątek.
        """
        # Symulacja błędu
        mock_get.side_effect = Exception("Boom!")

        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=1)
        data = med.fetch_external_info()

        # Metoda powinna zwrócić słownik z kluczem "error"
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Boom!")
