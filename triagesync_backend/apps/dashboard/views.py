from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.patients.models import PatientSubmission
from apps.authentication.permissions import IsMedicalStaff
from apps.core.response import success_response
from .serializers import DashboardPatientSerializer


class DashboardPatientListView(ListAPIView):
    serializer_class = DashboardPatientSerializer
    permission_classes = [IsAuthenticated, IsMedicalStaff]

    def get_queryset(self):
        queryset = PatientSubmission.objects.select_related("patient").order_by("-created_at")

        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return success_response(serializer.data)
