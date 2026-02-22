from tkinter.font import names

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apis.views.base import OrbatAPIView
from orbat.enums import OrbatActions
from orbat.models.sections import Section, SectionSlot, SectionSlotDetail


class SlotAPI(OrbatAPIView):
    """
    GET  -> Get slot list
    POST -> Create a new slot
    """
    required_permissions = {
        "POST": [OrbatActions.MODIFY_SECTION]
    }

    def get_object(self):
        return get_object_or_404(Section, pk=self.kwargs['section_id'])

    def get(self):
        pass

    def post(self, request, *args, **kwargs):
        section = self._object
        data = request.data

        name = (data.get("name") or "").strip()
        colour = data.get("colour")
        is_officer = bool(data.get("is_officer"))

        if not name:
            return Response(
                {"error": "Slot name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if colour not in {"Gold", "Green", "Red", "Blue"}:
            return Response(
                {"error": "Invalid colour."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Enforce section max size
        active_slot_count = section.slots.count()
        if active_slot_count >= section.max_size:
            return Response(
                {"error": "Section has reached its maximum size."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        today = timezone.now().date()

        # Officer uniqueness per colour
        if is_officer:
            conflict = (
                SectionSlotDetail.objects
                .filter(
                    slot__section=section,
                    colour=colour,
                    is_officer=True,
                    start_date__lte=today,
                )
                .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
                .first()
            )

            if conflict:
                return Response(
                    {
                        "error": (
                            f"{conflict.name} is already the officer "
                            f"for the {colour} team."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Create slot + initial detail atomically
        with transaction.atomic():
            slot = SectionSlot.objects.create(
                section=section,
            )

            SectionSlotDetail.objects.create(
                slot=slot,
                name=name,
                colour=colour,
                is_officer=is_officer,
                start_date=today,
            )

        return Response(
            {
                "success": True,
                "id": slot.pk,
            },
            status=status.HTTP_201_CREATED,
        )

class SlotDetailAPI(OrbatAPIView):
    """
    GET  -> Get slot details
    PUT  -> Update slot details
    """
    required_permissions = {
        "PUT": [OrbatActions.MODIFY_SECTION]
    }

    def get_object(self):
        return get_object_or_404(Section, pk=self.kwargs['section_id'])

    def get(self):
        pass

    def put(self, request, *args, **kwargs):
        section = self._object
        slot_id = self.kwargs['slot_id']

        slot = get_object_or_404(SectionSlot, pk=slot_id, section=section)

        data = request.data
        print(data)
        name = (data.get("name") or "").strip()
        colour = data.get("colour")
        is_officer = bool(data.get("is_officer"))

        if not name:
            return Response(
                {"error": "Slot name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if colour not in {"Gold", "Green", "Red", "Blue"}:
            return Response(
                {"error": "Invalid colour."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if slot.is_leader and not is_officer:
            return Response(
                {"error": "Leader slot must be an officer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        today = timezone.now().date()

        if is_officer:
            conflict = (
                SectionSlotDetail.objects
                .filter(
                    slot__section=slot.section,
                    colour=colour,
                    is_officer=True,
                    start_date__lte=today,
                )
                .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
                .exclude(slot=slot)
                .first()
            )

            if conflict:
                return Response(
                    {
                        "error": (
                            f"{conflict.name} is already the officer "
                            f"for the {colour} team."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        current_detail = SectionSlotDetail.objects.get(slot_id=slot_id, end_date__isnull=True)

        if current_detail is None:
            SectionSlotDetail.objects.create(
                slot_id=slot_id,
                name=name,
                colour=colour,
                is_officer=is_officer,
                start_date=today,
            )
            return Response({"success": True})

        if (
                current_detail.name == name
                and current_detail.colour == colour
                and current_detail.is_officer == is_officer

        ):
            return Response({"success": True})


        current_detail.end_date = today
        current_detail.save(update_fields=["end_date"])

        SectionSlotDetail.objects.create(
            slot=slot,
            name=name,
            colour=colour,
            is_officer=is_officer,
            start_date=today,
        )

        return Response({"success": True})