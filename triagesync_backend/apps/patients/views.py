from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import PatientSerializer

@api_view(['POST'])
def submit_triage(request):

    serializer = PatientSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response({"message":"Triage submitted"})

    return Response(serializer.errors)
