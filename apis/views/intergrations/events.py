from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apis.views.base import IntergrationAPIView
from intergrations.models import IntegrationEvent
from intergrations.permissions import IntergrationActions


class IntergrationsOpenEventsView(IntergrationAPIView):
    object_permission_required = False
    required_permissions = {
        "GET": [IntergrationActions.VIEW_EVENTS]
    }

    def get(self, request, *args, **kwargs):
        pass

class IntergrationsClaimEventView(IntergrationAPIView):
    """
    POST -> Try to claim the event returning the event payload
    """
    required_permissions = {
        "POST": [IntergrationActions.MANAGE_EVENTS]
    }

    def get_object(self):
        return get_object_or_404(IntegrationEvent, pk=self.kwargs['pk'] )

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            event = IntegrationEvent.objects.select_for_update().get(pk=self.kwargs['pk'])

            if not event.is_claimable:
                return Response({"error": "Event already processing or completed"}, status=status.HTTP_409_CONFLICT)
            event.status = IntegrationEvent.Status.PROCESSING
            event.processing_started = timezone.now()
            event.attempts += 1
            event.save(update_fields=["status", "processing_started", "attempts"])

        data = {
            "id": event.pk,
            "event_type": event.event_type,
            "created_at": event.created,
            "payload": event.payload,
        }

        return Response(data)

class IntergrationsSuccessEventView(IntergrationAPIView):
    """
    POST -> Try to claim the event returning the event payload
    """
    required_permissions = {
        "POST": [IntergrationActions.MANAGE_EVENTS]
    }

    def get_object(self):
        return get_object_or_404(IntegrationEvent, pk=self.kwargs['pk'] )

    def post(self, request, *args, **kwargs):
        event = self._object
        if event.status != IntegrationEvent.Status.PROCESSING:
            return Response(
                {"error": "Invalid state transition"},
                status=409
            )
        event.status = IntegrationEvent.Status.COMPLETED
        event.processing_completed = None
        event.save(update_fields=["status", "processing_started"])
        return Response({"success": True})

class IntergrationsErrorEventView(IntergrationAPIView):
    """
    POST -> Try to claim the event returning the event payload
    """
    required_permissions = {
        "POST": [IntergrationActions.MANAGE_EVENTS]
    }

    def get_object(self):
        return get_object_or_404(IntegrationEvent, pk=self.kwargs['pk'] )

    def post(self, request, *args, **kwargs):
        event = self._object
        if event.status != IntegrationEvent.Status.PROCESSING:
            return Response(
                {"error": "Invalid state transition"},
                status=409
            )
        event.error = request.data.get('error')
        event.status = IntegrationEvent.Status.ERRORED
        event.processing_completed = None
        event.save(update_fields=["error", "status", "processing_completed"])
        return Response({"success": True})