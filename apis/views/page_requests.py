from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from apis.views import BaseAPIView
from orbat.models import SectionSlot, RoleSlotAssignment, SectionAssignment, Role, Section


class SectionSlotAPI(BaseAPIView):
    def _serialize_slot(self, slot):
        role_assignments = RoleSlotAssignment.objects.filter(
            section_slot=slot, end_date__isnull=True
        ).select_related("role")

        inline_roles = [
            {"id": a.role.id, "name": a.role.name}
            for a in role_assignments
        ]

        data = {
            "id": slot.id,
            "name": slot.name,
            "colour": "",
            "member": slot.user.id if slot.user else None,
            "description": "",
            "order": slot.order,
            "inline_roles": inline_roles
        }
        return data

    def context_check(self, request, method, user, *args, **kwargs):
        # Allow GET to anyone
        if method == "GET":
            return True

        section_id = kwargs.get("section_id")
        if not section_id:
            return False
        section = get_object_or_404(Section, pk=section_id)

        has_permission = section.leader == user or user.is_staff
        if not has_permission:
            return False

        if method == "POST":
            return True

        # Check slot exists and belongs to the faction
        slot_id = kwargs.get("slot_id")
        if not slot_id:
            return False

        slot = get_object_or_404(SectionSlot, pk=slot_id)
        if section != slot.section:
            return False

        return True

    def get(self, request, section_id, slot_id):
        slot = get_object_or_404(SectionSlot, pk=slot_id)
        return Response(self._serialize_slot(slot), status=status.HTTP_200_OK)

    def post(self, request, section_id, slot_id=None): # Create a new slot
        if slot_id:
            return Response({"detail": "Use PUT to update existing slots."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate incoming data
        name = request.data.get("name")
        if not name:
            return Response({"name": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        section = get_object_or_404(Section, pk=section_id)

        slot = SectionSlot.objects.create(
            section=section,
            name=request.data.get("name", ""),
            user_id=request.data.get("member") or None
        )

        return Response(self._serialize_slot(slot), status=status.HTTP_201_CREATED)

    def put(self, request, section_id, slot_id):
        """Update an existing slot."""
        slot = get_object_or_404(SectionSlot, pk=slot_id)

        # Update fields
        name = request.data.get("name")
        if name:
            slot.name = name

        member_id = request.data.get("member")
        if member_id is not None:
            slot.user_id = member_id

        slot.save()

        return Response(self._serialize_slot(slot), status=status.HTTP_200_OK)

    def delete(self, request, section_id, slot_id):
        slot = get_object_or_404(SectionSlot, pk=slot_id)
        slot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SectionRoleOptions(BaseAPIView):
    def get(self, request, section_id):

        section = Section.objects.filter(pk=section_id).first()
        if not section:
            return Response({"detail": "Section not found"}, status=status.HTTP_404_NOT_FOUND)


        # Optional: allow ?slot_id=123 to account for inline roles in this slot
        slot_id = request.query_params.get("slot_id")
        inline_role_ids = set()
        if slot_id:
            role_assignments = RoleSlotAssignment.objects.filter(
                section_slot__pk=slot_id, end_date__isnull=True
            ).select_related("role")

            inline_role_ids = {r.role.id for r in role_assignments}

        roles = Role.objects.all().prefetch_related("allowed_sections", "incompatible_roles")

        section_role_counts = (
            RoleSlotAssignment.objects
            .filter(section_slot__section=section, end_date__isnull=True)
            .values("role")
            .annotate(count=Count("id"))
        )

        role_counts = {entry["role"]: entry["count"] for entry in section_role_counts}

        role_options = []
        for r in roles:
            # If no allowed_sections, role is globally allowed
            if r.allowed_sections.count() == 0 or r.allowed_sections.filter(pk=section_id).exists():

                current_count = role_counts.get(r.id, 0)

                is_capacity = False
                if r.max_per_section is not None and current_count >= r.max_per_section:
                    # If role not already selected inline for this slot, it's at capacity
                    if r.id not in inline_role_ids:
                        is_capacity = True

                role_options.append({
                    "id": r.id,
                    "name": r.name,
                    "shorthand": r.shorthand,
                    "is_rank": r.is_rank,
                    "is_capacity": is_capacity,
                    "conflicts": list(r.incompatible_roles.values_list("id", flat=True)),
                })

        return Response(role_options)


class SectionMembersAPI(BaseAPIView):
    def get(self, request, section_id):
        active_assignments = SectionAssignment.objects.filter(
            section_id=section_id, end_date__isnull=True
        ).select_related("user")

        members = [
            {
                'id': a.user.id,
                'name': a.user.get_ranked_name(),
            }
            for a in active_assignments if a.user
        ]
        return Response(members)