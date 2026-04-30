from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from triagesync_backend.apps.notifications.models import Notification, NotificationPreference
from triagesync_backend.apps.notifications.serializers import (
    NotificationPreferenceSerializer,
    NotificationSerializer,
)
from triagesync_backend.apps.core.response import success_response
from django.utils import timezone

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        is_read = self.request.query_params.get("is_read")
        notification_type = self.request.query_params.get("notification_type")
        if is_read is not None:
            queryset = queryset.filter(is_read=(is_read.lower() == "true"))
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        return queryset.order_by("-created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return Response({"data": paginated.data})
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data})

    @action(detail=True, methods=["patch"], url_path="read")
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
        serializer = self.get_serializer(notification)
        return Response({"data": serializer.data})

    @action(detail=False, methods=["patch"], url_path="read-all")
    def mark_all_as_read(self, request):
        queryset = self.get_queryset().filter(is_read=False)
        count = queryset.update(is_read=True, read_at=timezone.now())
        return Response({"data": {"message": "All notifications marked as read", "count": count}})

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"data": {"unread_count": count}})


class NotificationPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        preference, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(preference)
        return Response(serializer.data)

    def patch(self, request):
        preference, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(preference, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)
