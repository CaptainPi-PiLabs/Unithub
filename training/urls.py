from django.urls import path

from training.views.api_wrappers import *
from training.views.dashboard import TrainingHomeView
from training.views.matrix import TrainingMatrixView
from training.views.qualifications import QualificationsListView, QualificationDetailView

urlpatterns = [
    path("", TrainingHomeView.as_view(), name="training_home"),
    path("matrix/", TrainingMatrixView.as_view(), name="training_matrix"),
    path("qualifications/", QualificationsListView.as_view(), name="training_qualification_list"),
    path("qualifications/<int:qual_id>/", QualificationDetailView.as_view(), name="training_qualification_detail"),
    path("qualifications/<int:qual_id>/new_event/", QualificationDetailView.as_view(), name="training_create_event"),

    # Post mutation endpoints
    path("qualifications/create/", create_qualification, name="training_qualification_create"),
    path("qualifications/<int:qual_id>/save/", save_qualification, name="training_qualification_save"),
    path("qualifications/<int:qual_id>/remove/", remove_qualification, name="training_qualification_remove"),
    path("qualifications/<int:qual_id>/move/", move_qualification, name="training_qualification_move"),
    path("qualifications/<int:qual_id>/criteria/save/", save_criterion, name="training_qualification_criterion_save"),
    path("qualifications/<int:qual_id>/criteria/remove/", remove_criterion, name="training_qualification_criterion_remove"),
    path("qualifications/<int:qual_id>/criteria/move/", move_criterion, name="training_qualification_criterion_move"),
    path("qualifications/<int:qual_id>/trainers/save/", save_trainer, name="training_qualification_trainer_save"),
    path("qualifications/<int:qual_id>/trainers/remove/", remove_trainer, name="training_qualification_trainer_remove"),
]