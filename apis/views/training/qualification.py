from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from apis.views.base import TrainingAPIView
from training.enums import TrainingActions
from training.models import Qualification


class QualificationAPI(TrainingAPIView):
    """
    GET    -> Get details about a qualification.
    POST   -> Save a qualification.
    DELETE -> Remove a qualification.
    """

    required_permissions = {
        "GET": [TrainingActions.MODIFY_QUALIFICATION],
        "POST": [TrainingActions.MODIFY_QUALIFICATION],
        "DELETE": [TrainingActions.REMOVE_QUALIFICATION]
    }

    def get_object(self):
        return get_object_or_404(Qualification, pk=self.kwargs['qual_id'])

    def get(self, request, *args, **kwargs):
        qualification = self._object
        data = {
            "id": qualification.id,
            "name": qualification.name,
            "description": qualification.description,
            "criteria": []
        }
        for criterion in qualification.criterion_set.all():
            data["criteria"].append({
                "id": criterion.id,
                "name": criterion.name,
                "description": criterion.description,
                "order": criterion.order
            })
        return Response({"qualification": data})

    def post(self, request, *args, **kwargs):
        qualification = self._object
        data = request.data
        name = (data.get("name") or "").strip()
        if not name:
            return Response({"error": "Qualification name is required."}, status=status.HTTP_400_BAD_REQUEST)
        description = data.get("description", "").strip()
        qualification.name = name
        qualification.description = description
        qualification.save()
        return Response({"success": True, "id": qualification.id})

    def delete(self, request, *args, **kwargs):
        qualification = self._object
        qualification.delete()
        return Response({"success": True})

class CreateQualificationAPI(TrainingAPIView):
    """
    POST -> Create a new qualification
    """
    object_permission_required = False
    required_permissions = {
        "POST": [TrainingActions.CREATE_QUALIFICATION]
    }

    def post(self, request, *args, **kwargs):
        data = request.data
        name = (data.get("name") or "").strip()
        if not name:
            return Response({"error": "Qualification name is required."}, status=status.HTTP_400_BAD_REQUEST)

        description = data.get("description", "").strip()
        try:
            qualification = Qualification.objects.create(name=name, description=description)
        except IntegrityError:
            return Response({"error": f"A qualification named '{name}' already exists."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"success": True, "id": qualification.pk})

class QualificationMoveAPI(TrainingAPIView):
    """
    POST -> Move qualification (absolute or relative)
    """

    required_permissions = {
        "POST": [TrainingActions.MODIFY_QUALIFICATION],
    }

    def get_object(self):
        return get_object_or_404(Qualification, pk=self.kwargs["qual_id"])

    def post(self, request, *args, **kwargs):
        qualification = self._object
        data = request.data

        position = data.get("position")
        direction = data.get("direction")

        if position is not None and direction is not None:
            return Response({"error": "Use either position or direction, not both."}, status=status.HTTP_400_BAD_REQUEST)

        if position is not None:
            try:
                position = int(position)
            except (TypeError, ValueError):
                return Response({"error": "Invalid position"}, status=status.HTTP_400_BAD_REQUEST)

            qualification.move_to(position)
            return Response({"success": True})

        if direction == "up":
            qualification.move_up()
            return Response({"success": True})

        if direction == "down":
            qualification.move_down()
            return Response({"success": True})

        return Response({"error": "No valid move operation supplied."}, status=status.HTTP_400_BAD_REQUEST)