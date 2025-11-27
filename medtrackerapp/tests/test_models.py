import pytest
from django.test import TestCase
from medtrackerapp.models import Medication, DoseLog
from django.utils import timezone
from datetime import date, timedelta
from datetime import timedelta


class MedicationModelTests(TestCase):

    def test_str_returns_name_and_dosage(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        self.assertEqual(str(med), "Aspirin (100mg)")

    def test_adherence_rate_all_doses_taken(self):
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)

        now = timezone.now()
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=30))
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=1))

        adherence = med.adherence_rate()
        self.assertEqual(adherence, 100.0)

    def test_create_medication(self):
        med = Medication.objects.create(
            name="Ibuprofen",
            dosage_mg=200,
            prescribed_per_day=2
        )

        assert med.name == "Ibuprofen"
        assert med.dosage_mg == 200
        assert med.prescribed_per_day == 2
        assert str(med) == "Ibuprofen (200mg)"


    def test_doselog_create(self):
        med = Medication.objects.create(
            name="Test",
            dosage_mg=10,
            prescribed_per_day=1
        )

        log = DoseLog.objects.create(
            medication=med,
            taken_at=timezone.now(),
            was_taken=True
        )

        assert log.medication == med
        assert log.was_taken is True
        assert str(med.name) in str(log)


    def test_adherence_rate_no_logs(self):
        med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=1
        )

        assert med.adherence_rate() == 0.0


    def test_adherence_rate_with_logs(self):
        med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=1
        )

        DoseLog.objects.create(
            medication=med,
            taken_at=timezone.now(),
            was_taken=True
        )
        DoseLog.objects.create(
            medication=med,
            taken_at=timezone.now(),
            was_taken=False
        )

        assert med.adherence_rate() == 50.0


    def test_expected_doses(self):
        med = Medication.objects.create(
            name="Test",
            dosage_mg=100,
            prescribed_per_day=2
        )

        assert med.expected_doses(3) == 6

        with pytest.raises(ValueError):
            med.expected_doses(-1)


    def test_adherence_rate_over_period(self):
        med = Medication.objects.create(
            name="Test",
            dosage_mg=100,
            prescribed_per_day=1
        )

        today = date.today()
        yesterday = today - timedelta(days=1)

        DoseLog.objects.create(
            medication=med,
            taken_at=timezone.now() - timedelta(days=1),
            was_taken=True
        )

        result = med.adherence_rate_over_period(yesterday, today)
        assert result == 50.0  # 1 taken over 2 expected doses


        with pytest.raises(ValueError):
            med.adherence_rate_over_period(today, yesterday)


