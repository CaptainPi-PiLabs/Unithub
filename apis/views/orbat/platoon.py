from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from apis.views.base import OrbatAPIView
from orbat.enums import OrbatActions
from orbat.models.sections import Platoon, Section

class PlatoonAPI(OrbatAPIView):
    """
    GET   -> Get platoon list
    POST  -> Create a new platoon
    """
    object_permission_required = False
    required_permissions = {
        "POST": [OrbatActions.CREATE_PLATOON]
    }

    def post(self, request, *args, **kwargs):
        data = request.data
        name = (data.get("name") or "").strip()
        if not name:
            return Response({"error": "Qualification name is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            platoon = Platoon.objects.create(name=name)
        except IntegrityError:
            return Response({"error": f"A qualification named '{name}' already exists."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"success": True, "id": platoon.pk})

class PlatoonDetailAPI(OrbatAPIView):
    """
    GET   -> Get platoon information
    PUT   -> Update all required fields in a platoon
    PATCH -> Update limited fields in a platoon
    """

    required_permissions = {
        "GET": [OrbatActions.MODIFY_PLATOON],
        "POST": [OrbatActions.MODIFY_PLATOON],
    }

    def get_object(self):
        return get_object_or_404(Platoon, pk=self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        platoon = self._object

        sections = []
        for section in Section.objects.filter(platoon=platoon).order_by("order"):
            sections.append({
                "id": section.pk,
                "name": section.name,
            })
        data = {
            "id": platoon.pk,
            "name": platoon.name,
            "description": platoon.description,
            "sections": sections,
        }
        return Response(data)

    def put(self, request, *args, **kwargs):
        platoon = self._object
        data = request.data
        name = (data.get("name") or "").strip()
        if not name:
            return Response({"error": "Qualification name is required."}, status=status.HTTP_400_BAD_REQUEST)

        platoon.name = name
        platoon.save()
        return Response({"success": True, "id": platoon.pk})


class MovePlatoonAPI(OrbatAPIView):
    """
    POST  -> Move platoon (absolute or relative)
    """

    required_permissions = {
        "POST": [OrbatActions.MODIFY_PLATOON],
    }

    def get_object(self):
        return get_object_or_404(Platoon, pk=self.kwargs["qual_id"])

    def post(self, request, *args, **kwargs):
        platoon = self._object
        data = request.data

        position = data.get("position")
        direction = data.get("direction")

        if position is not None and direction is not None:
            return Response({"error": "Use either position or direction, not both."},
                            status=status.HTTP_400_BAD_REQUEST)

        if position is not None:
            try:
                position = int(position)
            except (TypeError, ValueError):
                return Response({"error": "Invalid position"}, status=status.HTTP_400_BAD_REQUEST)

            platoon.move_to(position)
            return Response({"success": True})

        if direction == "up":
            platoon.move_up()
            return Response({"success": True})

        if direction == "down":
            platoon.move_down()
            return Response({"success": True})

        return Response({"error": "No valid move operation supplied."}, status=status.HTTP_400_BAD_REQUEST)