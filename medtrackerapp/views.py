from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.utils.dateparse import parse_date
from .models import Medication, DoseLog, DoctorNote
from .serializers import MedicationSerializer, DoseLogSerializer, DoctorNoteSerializer

class MedicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing medications.

    Provides standard CRUD operations via the Django REST Framework
    `ModelViewSet`, as well as a custom action for retrieving
    additional information from an external API (OpenFDA).

    Endpoints:
        - GET /medications/ — list all medications
        - POST /medications/ — create a new medication
        - GET /medications/{id}/ — retrieve a specific medication
        - PUT/PATCH /medications/{id}/ — update a medication
        - DELETE /medications/{id}/ — delete a medication
        - GET /medications/{id}/info/ — fetch external drug info from OpenFDA
    """
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer

    @action(detail=True, methods=["get"], url_path="info")
    def get_external_info(self, request, pk=None):
        """
        Retrieve external drug information from the OpenFDA API.

        Calls the `Medication.fetch_external_info()` method, which
        delegates to the `DrugInfoService` for API access.

        Args:
            request (Request): The current HTTP request.
            pk (int): Primary key of the medication record.

        Returns:
            Response:
                - 200 OK: External API data returned successfully.
                - 502 BAD GATEWAY: If the external API request failed.

        Example:
            GET /medications/1/info/
        """
        medication = self.get_object()
        data = medication.fetch_external_info()

        if isinstance(data, dict) and data.get("error"):
            return Response(data, status=status.HTTP_502_BAD_GATEWAY)
        return Response(data)

    def _validate_positive_integer(self, param_name, param_value):
        """
        Validate that a query parameter is a positive integer.
        
        Args:
            param_name (str): Name of the parameter for error messages.
            param_value (str): The value to validate.
            
        Returns:
            int: The validated positive integer.
            
        Raises:
            ValidationError: If validation fails.
        """
        if not param_value:
            raise ValidationError(f"{param_name} parameter is required")
        
        try:
            value = int(param_value)
            if value <= 0:
                raise ValidationError(f"{param_name} must be a positive integer")
            return value
        except ValueError:
            raise ValidationError(f"{param_name} must be a valid integer")

    @action(detail=True, methods=["get"], url_path="expected-doses")
    def expected_doses(self, request, pk=None):
        """
        Calculate expected doses for a medication over a given number of days.
        
        Query Parameters:
            days (int): Number of days (must be positive integer).
            
        Args:
            request (Request): The current HTTP request.
            pk (int): Primary key of the medication record.
            
        Returns:
            Response:
                - 200 OK: Contains medication_id, days, and expected_doses.
                - 400 BAD REQUEST: If days parameter is missing, invalid, or calculation fails.
                
        Example:
            GET /medications/1/expected-doses/?days=7
            Response: {"medication_id": 1, "days": 7, "expected_doses": 14}
        """
        medication = self.get_object()
        
        try:
            days = self._validate_positive_integer("days", request.query_params.get("days"))
            expected = medication.expected_doses(days)
            
            return Response({
                "medication_id": medication.pk,
                "days": days,
                "expected_doses": expected
            }, status=status.HTTP_200_OK)
            
        except (ValidationError, ValueError) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class DoseLogViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing dose logs.

    A DoseLog represents an event where a medication dose was either
    taken or missed. This viewset provides standard CRUD operations
    and a custom filtering action by date range.

    Endpoints:
        - GET /logs/ — list all dose logs
        - POST /logs/ — create a new dose log
        - GET /logs/{id}/ — retrieve a specific log
        - PUT/PATCH /logs/{id}/ — update a dose log
        - DELETE /logs/{id}/ — delete a dose log
        - GET /logs/filter/?start=YYYY-MM-DD&end=YYYY-MM-DD —
          filter logs within a date range
    """
    queryset = DoseLog.objects.all()
    serializer_class = DoseLogSerializer

    @action(detail=False, methods=["get"], url_path="filter")
    def filter_by_date(self, request):
        """
        Retrieve all dose logs within a given date range.

        Query Parameters:
            - start (YYYY-MM-DD): Start date of the range (inclusive).
            - end (YYYY-MM-DD): End date of the range (inclusive).

        Returns:
            Response:
                - 200 OK: A list of dose logs between the two dates.
                - 400 BAD REQUEST: If start or end parameters are missing or invalid.

        Example:
            GET /logs/filter/?start=2025-11-01&end=2025-11-07
        """
        start_str = request.query_params.get("start")
        end_str = request.query_params.get("end")

        if not start_str or not end_str:
            return Response(
                {"error": "Both 'start' and 'end' query parameters are required and must be valid dates."},
                status=status.HTTP_400_BAD_REQUEST
            )

        start = parse_date(start_str)
        end = parse_date(end_str)

        if not start or not end:
            return Response(
                {"error": "Both 'start' and 'end' query parameters are required and must be valid dates."},
                status=status.HTTP_400_BAD_REQUEST
            )

        logs = self.get_queryset().filter(
            taken_at__date__gte=start,
            taken_at__date__lte=end
        ).order_by("taken_at")

        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)


class DoctorNoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing doctor's notes.

    Provides operations to create, retrieve, list, and delete notes.
    Updating notes is not supported (PUT/PATCH return 405).

    Each note is associated with a medication and contains text observations
    along with an auto-generated creation timestamp.

    Endpoints:
        - GET /notes/ — list all notes (ordered by creation date, newest first)
        - POST /notes/ — create a new note
        - GET /notes/{id}/ — retrieve a specific note
        - DELETE /notes/{id}/ — delete a note

    Query Parameters:
        - medication: Filter notes by medication ID (e.g., ?medication=1)

    Examples:
        GET /api/notes/
        GET /api/notes/?medication=5
        POST /api/notes/ {"medication": 1, "text": "Patient responding well"}
        DELETE /api/notes/3/
    """
    queryset = DoctorNote.objects.all()
    serializer_class = DoctorNoteSerializer
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    
    def get_queryset(self):
        """
        Optionally filter notes by medication ID.
        
        Returns:
            QuerySet: Filtered or full list of notes.
        """
        queryset = super().get_queryset()
        medication_id = self.request.query_params.get('medication')
        
        if medication_id is not None:
            queryset = queryset.filter(medication_id=medication_id)
        
        return queryset
