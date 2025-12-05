from unittest.mock import patch
from django.test import TestCase
from medtrackerapp.models import Medication
from medtrackerapp.services import DrugInfoService


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

    @patch("medtrackerapp.services.requests.get")
    def test_successful_api_response(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "results": [
                {
                    "openfda": {
                        "generic_name": ["Aspirin"],
                        "manufacturer_name": ["Bayer"]
                    },
                    "warnings": ["Test warning"],
                    "purpose": ["Pain relief"],
                }
            ]
        }

        data = DrugInfoService.get_drug_info("Aspirin")
        self.assertEqual(data["name"], "Aspirin")
        self.assertEqual(data["manufacturer"], "Bayer")
        self.assertEqual(data["warnings"], ["Test warning"])
        self.assertEqual(data["purpose"], ["Pain relief"])

    @patch("medtrackerapp.services.requests.get")
    def test_api_non_200_status(self, mock_get):
        mock_get.return_value.status_code = 404
        with self.assertRaises(ValueError):
            DrugInfoService.get_drug_info("Aspirin")

    @patch("medtrackerapp.services.requests.get")
    def test_no_results(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"results": []}

        with self.assertRaises(ValueError):
            DrugInfoService.get_drug_info("Aspirin")

    @patch("medtrackerapp.services.requests.get")
    def test_api_exception(self, mock_get):
        mock_get.side_effect = Exception("Boom!")

        with self.assertRaises(Exception):
            DrugInfoService.get_drug_info("Aspirin")

    def test_missing_drug_name(self):
        with self.assertRaises(ValueError):
            DrugInfoService.get_drug_info("")