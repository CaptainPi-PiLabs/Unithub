from django.urls import path

from apis.views.training.criterion import *
from apis.views.training.qualification import *
from apis.views.training.trainer import *

urlpatterns = [
    path("qualification/<int:qual_id>/",QualificationAPI.as_view(), name="api-training-qualification"),
    path("qualification/create/",CreateQualificationAPI.as_view(), name="api-training-qualification-create"),
    path("qualification/<int:qual_id>/move/", QualificationMoveAPI.as_view(), name="api-training-qualification-move"),
    path("qualification/<int:qual_id>/criterion/", CriterionAPI.as_view(), name="api-training-qualification-criterion"),
    path("qualification/<int:qual_id>/criterion/move/", CriterionMoveAPI.as_view(), name="api-training-qualification-criterion-move"),
    path("qualification/<int:qual_id>/trainers", TrainerAPI.as_view(),name="api-training-qualification-trainer")
]
