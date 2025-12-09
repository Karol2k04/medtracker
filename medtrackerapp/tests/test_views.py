from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APITestCase
from django.urls import reverse
from medtrackerapp.models import Medication, DoseLog


class MedicationViewTests(APITestCase):
    def setUp(self):
        self.med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2
        )

    def test_list_medications_valid_data(self):
        url = reverse("medication-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_get_single_medication(self):
        url = reverse("medication-detail", args=[self.med.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_create_medication_valid(self):
        url = reverse("medication-list")
        data = {"name": "Ibuprofen", "dosage_mg": 200, "prescribed_per_day": 1}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 201)

    def test_create_medication_invalid(self):
        url = reverse("medication-list")
        data = {"name": "X"}  # brak wymaganych pól
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 400)

    def test_update_medication(self):
        url = reverse("medication-detail", args=[self.med.id])
        data = {
            "name": "Updated",
            "dosage_mg": 150,
            "prescribed_per_day": 1
        }
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, 200)

    def test_delete_medication(self):
        url = reverse("medication-detail", args=[self.med.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)


class MedicationInfoActionTests(APITestCase):
    def setUp(self):
        self.med = Medication.objects.create(
            name="Aspirin", dosage_mg=100, prescribed_per_day=1
        )

    @patch("medtrackerapp.models.DrugInfoService.get_drug_info")
    def test_external_info_success(self, mock_api):
        mock_api.return_value = {"name": "Aspirin"}

        url = reverse("medication-get-external-info", args=[self.med.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["name"], "Aspirin")

    @patch("medtrackerapp.services.DrugInfoService.get_drug_info")
    def test_external_info_error(self, mock_api):
        mock_api.return_value = {"error": "Failure"}

        url = reverse("medication-get-external-info", args=[self.med.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 502)
        self.assertIn("error", res.data)


class DoseLogViewTests(APITestCase):
    def setUp(self):
        self.med = Medication.objects.create(
            name="TestMed",
            dosage_mg=50,
            prescribed_per_day=1
        )

    def test_create_log(self):
        url = reverse("doselog-list")
        data = {
            "medication": self.med.id,
            "taken_at": timezone.now(),
            "was_taken": True
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(DoseLog.objects.count(), 1)

    def test_filter_logs_success(self):
        now = timezone.now()
        DoseLog.objects.create(medication=self.med, taken_at=now, was_taken=True)

        url = reverse("doselog-filter-by-date")
        response = self.client.get(url, {
            "start": (now - timedelta(days=1)).date(),
            "end": (now + timedelta(days=1)).date()
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_filter_logs_invalid(self):
        url = reverse("doselog-filter-by-date")
        response = self.client.get(url, {"start": "2024-10-10"})

        self.assertEqual(response.status_code, 400)
