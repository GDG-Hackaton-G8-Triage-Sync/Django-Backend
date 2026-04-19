
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

from .services.dashboard_service import update_patient_status


class UpdatePatientStatusView(APIView):
    """
    PATCH /api/dashboard/staff/patient/{id}/status/
    """

    def patch(self, request, id):
        status = request.data.get("status")

        patient = update_patient_status(id, status)

        if not patient:
            return Response({"error": "Patient not found"}, status=404)

        return Response({"message": "Status updated"})
    
from .services.dashboard_service import get_admin_overview


class AdminOverviewView(APIView):
    """
    GET /api/dashboard/admin/overview/
    """

    def get(self, request):
        data = get_admin_overview()
        return Response(data)