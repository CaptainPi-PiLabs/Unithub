from django.urls import path

from training.views import TrainingHomeView, TrainingMatrixView, QualificationDetailView
from training.views import QualificationsListView, TrainingManagementEditView, TrainingManagementCreateView

urlpatterns = [
    path("", TrainingHomeView.as_view(), name="training_home"),
    path("matrix/", TrainingMatrixView.as_view(), name="training_matrix"),
    path("qualifications/", QualificationsListView.as_view(), name="qualifications_list"),
    path("qualification/<int:pk>/", QualificationDetailView.as_view(), name="qualification_detail"),
    path("qualification/<int:pk>/edit/", TrainingManagementEditView.as_view(), name="qualification_edit"),
    path("qualification/<int:pk>/criteria_edit/", TrainingManagementEditView.as_view(), name="qualification_criteria_edit"),
    path("qualification/<int:pk>/trainer_edit/", TrainingManagementEditView.as_view(), name="qualification_trainer_edit"),
    path("qualification/<int:pk>/create_event/", QualificationDetailView.as_view(), name="training_create_event"),
    path("qualification/create/", TrainingManagementCreateView.as_view(), name="qualification_create"),
]