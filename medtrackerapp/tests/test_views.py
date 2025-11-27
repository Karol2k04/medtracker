from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APITestCase
from medtrackerapp.models import Medication, DoseLog
from django.urls import reverse
from rest_framework import status


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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Aspirin")
        self.assertEqual(response.data[0]["dosage_mg"], 100)

    def test_get_single_medication(self):
        url = reverse("medication-detail", args=[self.med.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Aspirin")

    def test_create_medication_valid(self):
        url = reverse("medication-list")
        data = {"name": "Ibuprofen", "dosage_mg": 200, "prescribed_per_day": 1}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Medication.objects.count(), 2)

    def test_create_medication_invalid(self):
        url = reverse("medication-list")
        data = {"name": "Bad"}  # brak wymaganych pól

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
        self.assertEqual(response.data["name"], "Updated")

    def test_delete_medication(self):
        url = reverse("medication-detail", args=[self.med.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(Medication.objects.count(), 0)


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

    def test_filter_logs(self):
        now = timezone.now()
        DoseLog.objects.create(medication=self.med, taken_at=now, was_taken=True)

        url = reverse("doselog-list")
        response = self.client.get(url, {
            "start": (now - timedelta(days=1)).date(),
            "end": (now + timedelta(days=1)).date()
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_filter_logs_invalid_dates(self):
        url = reverse("doselog-list")
        response = self.client.get(url, {"start": "2022-10-10"})
        self.assertEqual(response.status_code, 200)
