from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from medtrackerapp.models import Medication, DoctorNote


class DoctorNoteTests(APITestCase):
    def setUp(self):
        """Set up test data - create a medication for testing"""
        self.medication = Medication.objects.create(
            name="Test Medication",
            dosage_mg=100,
            prescribed_per_day=2
        )
        self.medication2 = Medication.objects.create(
            name="Another Med",
            dosage_mg=50,
            prescribed_per_day=1
        )
        
    def test_create_note_success(self):
        """Test successfully creating a doctor's note"""
        url = reverse('doctornote-list')
        data = {
            'medication': self.medication.id,
            'text': 'Patient shows good response to medication'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DoctorNote.objects.count(), 1)
        self.assertEqual(response.data['text'], 'Patient shows good response to medication')
        self.assertEqual(response.data['medication'], self.medication.id)
        self.assertIn('created_at', response.data)
        self.assertIn('id', response.data)
    
    def test_create_note_missing_text(self):
        """Test creating a note without text field fails"""
        url = reverse('doctornote-list')
        data = {
            'medication': self.medication.id
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('text', response.data)
    
    def test_create_note_missing_medication(self):
        """Test creating a note without medication field fails"""
        url = reverse('doctornote-list')
        data = {
            'text': 'Some note text'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('medication', response.data)
    
    def test_create_note_invalid_medication(self):
        """Test creating a note with non-existent medication ID fails"""
        url = reverse('doctornote-list')
        data = {
            'medication': 99999,
            'text': 'Some note text'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_list_notes(self):
        """Test retrieving list of all notes"""
        # Create some notes
        DoctorNote.objects.create(
            medication=self.medication,
            text='First note'
        )
        DoctorNote.objects.create(
            medication=self.medication2,
            text='Second note'
        )
        
        url = reverse('doctornote-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_list_notes_empty(self):
        """Test retrieving empty list when no notes exist"""
        url = reverse('doctornote-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_retrieve_note(self):
        """Test retrieving a specific note by ID"""
        note = DoctorNote.objects.create(
            medication=self.medication,
            text='Detailed medical observation'
        )
        
        url = reverse('doctornote-detail', kwargs={'pk': note.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], 'Detailed medical observation')
        self.assertEqual(response.data['medication'], self.medication.id)
        self.assertEqual(response.data['id'], note.id)
    
    def test_retrieve_note_not_found(self):
        """Test retrieving a non-existent note returns 404"""
        url = reverse('doctornote-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_delete_note(self):
        """Test deleting a note"""
        note = DoctorNote.objects.create(
            medication=self.medication,
            text='Note to be deleted'
        )
        
        self.assertEqual(DoctorNote.objects.count(), 1)
        
        url = reverse('doctornote-detail', kwargs={'pk': note.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(DoctorNote.objects.count(), 0)
    
    def test_delete_note_not_found(self):
        """Test deleting a non-existent note returns 404"""
        url = reverse('doctornote-detail', kwargs={'pk': 99999})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_note_not_allowed_put(self):
        """Test that PUT update is not allowed (405 Method Not Allowed)"""
        note = DoctorNote.objects.create(
            medication=self.medication,
            text='Original text'
        )
        
        url = reverse('doctornote-detail', kwargs={'pk': note.id})
        data = {
            'medication': self.medication.id,
            'text': 'Updated text'
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_update_note_not_allowed_patch(self):
        """Test that PATCH update is not allowed (405 Method Not Allowed)"""
        note = DoctorNote.objects.create(
            medication=self.medication,
            text='Original text'
        )
        
        url = reverse('doctornote-detail', kwargs={'pk': note.id})
        data = {
            'text': 'Updated text'
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_notes_for_specific_medication(self):
        """Test filtering notes for a specific medication"""
        # Create notes for different medications
        note1 = DoctorNote.objects.create(
            medication=self.medication,
            text='Note for medication 1'
        )
        note2 = DoctorNote.objects.create(
            medication=self.medication,
            text='Another note for medication 1'
        )
        note3 = DoctorNote.objects.create(
            medication=self.medication2,
            text='Note for medication 2'
        )
        
        # Get all notes and verify we can identify them by medication
        url = reverse('doctornote-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Count notes for medication 1
        med1_notes = [n for n in response.data if n['medication'] == self.medication.id]
        self.assertEqual(len(med1_notes), 2)
        
        # Count notes for medication 2
        med2_notes = [n for n in response.data if n['medication'] == self.medication2.id]
        self.assertEqual(len(med2_notes), 1)
    
    def test_created_at_is_auto_generated(self):
        """Test that created_at field is automatically set"""
        note = DoctorNote.objects.create(
            medication=self.medication,
            text='Test note'
        )
        
        self.assertIsNotNone(note.created_at)
        
        url = reverse('doctornote-detail', kwargs={'pk': note.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('created_at', response.data)
        self.assertIsNotNone(response.data['created_at'])
    
    def test_created_at_is_read_only(self):
        """Test that created_at cannot be set manually during creation"""
        url = reverse('doctornote-list')
        data = {
            'medication': self.medication.id,
            'text': 'Test note',
            'created_at': '2020-01-01T00:00:00Z'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # created_at should be auto-generated, not the one we tried to set
        self.assertNotEqual(response.data['created_at'][:10], '2020-01-01')
