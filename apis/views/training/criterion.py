from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from apis.views.base import TrainingAPIView
from training.enums import TrainingActions
from training.models import Qualification, QualificationCriterion


class CriterionAPI(TrainingAPIView):
    """
    POST   -> Save a criterion
    DELETE -> Remove a criterion
    """

    required_permissions = {
        "POST": [TrainingActions.MODIFY_CRITERIA],
        "DELETE": [TrainingActions.REMOVE_CRITERIA],
    }

    def get_object(self):
        return get_object_or_404(Qualification, pk=self.kwargs["qual_id"])

    def post(self, request, *args, **kwargs):
        qualification = self._object
        data = request.data
        criterion_id = data.get("criterion_id")

        if criterion_id:
            criterion = get_object_or_404(QualificationCriterion, pk=criterion_id, qualification=qualification)
        else:
            criterion = QualificationCriterion(qualification=qualification)

        criterion.name = (data.get("name") or "").strip()
        criterion.description = (data.get("description") or "").strip()
        criterion.save()
        return Response({"success": True, "id": criterion.id})

    def delete(self, request, *args, **kwargs):
        qualification = self._object
        criterion_id = request.data.get("criterion_id")
        criterion = get_object_or_404(QualificationCriterion, pk=criterion_id, qualification=qualification)
        criterion.delete()
        return Response({"success": True})

class CriterionMoveAPI(TrainingAPIView):
    required_permissions = {
        "POST": [TrainingActions.MODIFY_CRITERIA],
    }

    def get_object(self):
        return get_object_or_404(Qualification, pk=self.kwargs["qual_id"])

    def post(self, request, *args, **kwargs):
        qualification = self._object
        data = request.data

        criterion_id = data.get("criterion_id")
        if not criterion_id:
            return Response({"error": "criterion_id required"}, status=status.HTTP_400_BAD_REQUEST)

        criterion = get_object_or_404(
            QualificationCriterion,
            pk=criterion_id,
            qualification=qualification,
        )

        position = data.get("position")
        direction = data.get("direction")

        if position is not None and direction is not None:
            return Response({"error": "Use either position or direction, not both."}, status=status.HTTP_400_BAD_REQUEST)

        if position is not None:
            criterion.move_to(int(position))
            return Response({"success": True})

        if direction == "up":
            criterion.move_up()
            return Response({"success": True})

        if direction == "down":
            criterion.move_down()
            return Response({"success": True})

        return Response({"error": "Invalid move request"}, status=status.HTTP_400_BAD_REQUEST)