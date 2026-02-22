from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.response import Response

from apis.views.base import OrbatAPIView
from orbat.enums import OrbatActions


User = get_user_model()

class SectionMembershipAPI(OrbatAPIView):
    """
    GET    -> List members
    POST   -> Add member(s)
    DELETE -> Remove member(s)
    """

    required_permissions = {
        "GET": [OrbatActions.MODIFY_SECTION],
        "POST": [OrbatActions.MODIFY_SECTION],
        "DELETE": [OrbatActions.MODIFY_SECTION],
    }

    def get_object(self):
        return get_object_or_404(Section, slug=self.kwargs["section_slug"])

    def get(self, request, *args, **kwargs):
        section = self._object
        members = SectionAssignment.objects.filter(section=section, end_date__isnull=True).select_related("user")
        data = [
            {"id": m.user.id, "name": m.user.get_ranked_name(), "joined": m.start_date}
            for m in members
        ]
        return Response({"members": data})

    def post(self, request, *args, **kwargs):
        section = self._object
        user_ids = request.data.get("user_ids", [])
        if not isinstance(user_ids, list):
            user_ids = [user_ids]

        created = []
        for uid in user_ids:
            user = get_object_or_404(User, pk=uid)
            if SectionAssignment.objects.filter(
                    section=section,
                    user=user,
                    end_date__isnull=True
            ).exists():
                continue
            SectionAssignment.objects.create(section=section, user=user)
            created.append(uid)

        return Response({"added": created}, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        section = self._object
        user_ids = request.data.get("user_ids", [])
        if not isinstance(user_ids, list):
            user_ids = [user_ids]

        removed = []
        for uid in user_ids:
            user = get_object_or_404(User, pk=uid)

            if section.leader == user:
                section.leader = None
                section.save(update_fields=["leader"])

            assignment = SectionAssignment.objects.filter(
                section=section,
                user_id=uid,
                end_date__isnull=True
            ).first()

            if assignment:
                assignment.end_date = timezone.now()
                assignment.save(update_fields=["end_date"])
                removed.append(uid)

        return Response({"removed": removed}, status=status.HTTP_200_OK)

class SectionLeaveAPI(OrbatAPIView):
    """
    POST -> Leave a section (self only)
    """

    required_permissions = {
        "POST": [OrbatActions.LEAVE_SECTION], # Policy-backed permission: allowed only if user is a member of the section
    }

    def get_object(self):
        return get_object_or_404(Section, slug=self.kwargs["section_slug"])

    def post(self, request, *args, **kwargs):
        user = request.effective_user
        section = self._object

        if not user:
            raise NotAuthenticated()

        assignment = SectionAssignment.objects.filter(
            section=section,
            user=user,
            end_date__isnull=True
        ).first()

        if not assignment:
            raise PermissionDenied("Not a member of this section")

        if section.leader == user:
            section.leader = None
            section.save(update_fields=["leader"])

        assignment.end_date = timezone.now()
        assignment.save(update_fields=["end_date"])

        return Response({"success": True})