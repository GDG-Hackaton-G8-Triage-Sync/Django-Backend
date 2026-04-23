from rest_framework.generics import ListAPIView

from apps.patients.models import PatientSubmission

from .serializers import DashboardPatientSerializer


class DashboardPatientListView(ListAPIView):
    queryset = PatientSubmission.objects.select_related("patient").order_by("-created_at")
    serializer_class = DashboardPatientSerializer
