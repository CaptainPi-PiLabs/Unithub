from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apis.views.base import OrbatAPIView
from orbat.enums import OrbatActions
from orbat.helpers import get_section_slot_snapshots
from orbat.models.sections import Section, Platoon


class SectionAPI(OrbatAPIView):
    """
    GET  -> Get section list
    POST -> Create a new section
    """
    object_permission_required = False
    required_permissions = {
        "GET": [OrbatActions.MODIFY_SECTION],
        "POST": [OrbatActions.CREATE_SECTION]
    }

    def get(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        data = request.data
        name = (data.get("name") or "").strip()
        if not name:
            return Response({"error": "Section name is required."}, status=status.HTTP_400_BAD_REQUEST)

        platoon_id = data.get("platoon_id")
        platoon = None
        if platoon_id:
            platoon = Platoon.objects.get(pk=platoon_id)
            if not platoon:
                return Response({"error": "Platoon does not exist."}, status=status.HTTP_404_NOT_FOUND)
        try:
            section = Section.objects.create(
                name=data.get("name", "").strip(),
                description=data.get("description", ""),
                shorthand=data.get("shorthand", "").strip(),
                max_size=data.get("max_size"),
                platoon=platoon
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"success": True, "id": section.pk})

class SectionDetailAPI(OrbatAPIView):
    """
    GET -> Get section details
    PUT -> Update section details
    """
    required_permissions = {
        "PUT": [OrbatActions.MODIFY_SECTION]
    }

    def get_object(self):
        return get_object_or_404(Section, pk=self.kwargs['section_id'])

    def get(self, request, *args, **kwargs):
        section = self._object

        date = timezone.now()

        section_slots = []
        for slot in get_section_slot_snapshots(section, date):
            section_slots.append({
                "id": slot["id"],
                "name": slot["name"],
                "colour": slot["colour"],
                "user_id": slot["user_id"],
                "user_name": slot["user_display_name"],
                "is_leader": slot["is_leader"],
                "is_officer": slot["is_officer"],
                "first_joined": slot.assignment["first_joined"],
                "start_date": slot.assignment["start_date"],
                "end_date": slot.assignment["end_date"],
            })

        data = {
            "id": section.pk,
            "name": section.name,
            "section_slots": section_slots,
        }
        return Response(data)

    def put(self, request, *args, **kwargs):
        section = self._object
        data = request.data
        name = (data.get("name") or "").strip()
        if not name:
            return Response({"error": "Qualification name is required."}, status=status.HTTP_400_BAD_REQUEST)

        section.name = name
        section.save()

        return Response({"success": True, "id": section.pk})

class MoveSectionAPI(OrbatAPIView):
    """
    POST -> Move section (absolute or relative)
    """

    object_permission_required = False
    required_permissions = {
        "POST": [OrbatActions.MODIFY_PLATOON],
    }

    def get_object(self):
        return get_object_or_404(Section, pk=self.kwargs['section_id'])

    def post(self, request, *args, **kwargs):
        section = self.get_object()
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

            section.move_to(position)
            return Response({"success": True})

        if direction == "up":
            section.move_up()
            return Response({"success": True})

        if direction == "down":
            section.move_down()
            return Response({"success": True})

        return Response({"error": "No valid move operation supplied."}, status=status.HTTP_400_BAD_REQUEST)