from unittest.mock import patch
from django.test import TestCase
from medtrackerapp.models import Medication

class DrugInfoMockTests(TestCase):

    @patch("medtrackerapp.models.DrugInfoService.get_drug_info")
    def test_fetch_external_info_success(self, mock_api):

        mock_api.return_value = {
            "name": "Aspirin",
            "manufacturer": "Unknown",
            "warnings": ["No warnings available"],
            "purpose": ["Not specified"]
        }

        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=1)
        data = med.fetch_external_info()

        self.assertIn("name", data)
        self.assertEqual(data["name"], "Aspirin")

    @patch("medtrackerapp.models.DrugInfoService.get_drug_info")
    def test_fetch_external_info_error(self, mock_api):

        mock_api.side_effect = Exception("Boom!")

        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=1)
        data = med.fetch_external_info()

        self.assertIn("error", data)
        self.assertEqual(data["error"], "Boom!")
