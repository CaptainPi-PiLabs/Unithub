from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from apis.views.base import TrainingAPIView
from training.enums import TrainingActions
from training.models import QualificationTrainer, Qualification


class TrainerAPI(TrainingAPIView):
    """
    POST   -> Save or create trainer
    DELETE -> Remove trainer
    """

    required_permissions = {
        "POST": [TrainingActions.MANAGE_TRAINERS],
        "DELETE": [TrainingActions.MANAGE_TRAINERS],
    }

    def get_object(self):
        return get_object_or_404(Qualification, pk=self.kwargs["qual_id"])

    def post(self, request, *args, **kwargs):
        qualification = self._object
        trainer_id = request.data.get("trainer_id")

        if trainer_id:
            trainer = get_object_or_404(QualificationTrainer, pk=trainer_id, qualification=qualification)
        else:
            trainer = QualificationTrainer(qualification=qualification)

        trainer.user_id = request.data.get("user_id")
        trainer.is_senior = bool(request.data.get("is_senior"))
        trainer.is_trainer = trainer.is_senior or bool(request.data.get("is_trainer"))
        trainer.save()
        return Response({"success": True, "id": trainer.id})

    def delete(self, request, *args, **kwargs):
        qualification = self._object
        trainer_id = request.data.get("trainer_id")
        trainer = get_object_or_404(QualificationTrainer, pk=trainer_id, qualification=qualification)
        trainer.delete()
        return Response({"success": True})