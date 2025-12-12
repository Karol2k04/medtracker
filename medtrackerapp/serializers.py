from rest_framework import serializers
from .models import Medication, DoseLog, DoctorNote

class MedicationSerializer(serializers.ModelSerializer):
    adherence = serializers.SerializerMethodField()

    class Meta:
        model = Medication
        fields = ["id", "name", "dosage_mg", "prescribed_per_day", "adherence"]

    def get_adherence(self, obj):
        return obj.adherence_rate()


class DoseLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoseLog
        fields = ["id", "medication", "taken_at", "was_taken"]


class DoctorNoteSerializer(serializers.ModelSerializer):
    """
    Serializer for DoctorNote model.
    
    Handles validation and serialization of doctor's notes.
    The created_at field is read-only and auto-generated.
    """
    
    class Meta:
        model = DoctorNote
        fields = ["id", "medication", "text", "created_at"]
        read_only_fields = ["created_at"]
    
    def validate_text(self, value):
        """
        Validate that note text is not empty or just whitespace.
        
        Args:
            value (str): The text content of the note.
            
        Returns:
            str: The validated text.
            
        Raises:
            serializers.ValidationError: If text is empty or whitespace only.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Note text cannot be empty.")
        return value.strip()
