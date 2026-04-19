
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import DashboardPatientSerializer
from .services.dashboard_service import get_patient_queue


class StaffPatientQueueView(APIView):
    """
    GET /api/dashboard/staff/patients/
    """

    def get(self, request):
        priority = request.query_params.get("priority")
        status = request.query_params.get("status")

        patients = get_patient_queue(priority, status)
        serializer = DashboardPatientSerializer(patients, many=True)

        return Response(serializer.data)
