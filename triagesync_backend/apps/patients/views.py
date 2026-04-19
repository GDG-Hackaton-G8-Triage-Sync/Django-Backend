from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import PatientSubmissionSerializer
from rest_framework.permissions import IsAuthenticated


class PatientSubmissionView(APIView):
    permission_classes = [IsAuthenticated] 
    def post(self, request):
        serializer = PatientSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
