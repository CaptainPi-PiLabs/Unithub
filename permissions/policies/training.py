from training.enums import TrainingActions
from training.models import QualificationTrainer
from .base import PermissionPolicy
from ..models import PermissionModule


class TrainingPolicy(PermissionPolicy):
    module = PermissionModule.TRAINING

class TrainerPolicy(TrainingPolicy):
    actions = {
        TrainingActions.GRANT_CERTIFICATE
    }

    def check(self, user, scope):
        if scope is None:
            return None

        if QualificationTrainer.objects.filter(
            user_id=user.id,
            qualification=scope,
            is_trainer=True
        ).exists():
            return True
        return None

class SeniorTrainerPolicy(TrainingPolicy):
    actions = {
        TrainingActions.ADD_CRITERIA,
        TrainingActions.MODIFY_CRITERIA,
    }

    def check(self, user, scope):
        if scope is None:
            return None

        if QualificationTrainer.objects.filter(
            user_id=user.id,
            qualification=scope,
            is_senior=True
        ).exists():
            return True
        return None

class ManagerTrainerPolicy(TrainingPolicy):
    actions = {
        TrainingActions.MODIFY_QUALIFICATION,
        TrainingActions.MANAGE_TRAINERS,
    }

    def check(self, user, scope):
        if scope is None:
            return None

        if QualificationTrainer.objects.filter(
            user_id=user.id,
            qualification=scope,
            is_manager=True
        ).exists():
            return True
        return None