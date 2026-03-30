from django.urls import path

from training.views.dashboard import TrainingHomeView
from training.views.matrix import TrainingMatrixView
from training.views.qualification_grant import TrainingQualificationGrantView
from training.views.qualifications import QualificationsListView, QualificationDetailView

urlpatterns = [
    path("", TrainingHomeView.as_view(), name="training_home"),
    path("matrix/", TrainingMatrixView.as_view(), name="training_matrix"),
    path("qualifications/", QualificationsListView.as_view(), name="training_qualification_list"),
    path("qualifications/<int:qual_id>/", QualificationDetailView.as_view(), name="training_qualification_detail"),
    path("qualifications/<int:qual_id>/grant/", TrainingQualificationGrantView.as_view(), name="training_qualification_grant"),
    path("qualifications/<int:qual_id>/new_event/", QualificationDetailView.as_view(), name="training_create_event"),
]