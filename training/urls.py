from django.urls import path

from training.views import TrainingHomeView, TrainingMatrixView

urlpatterns = [
    path("", TrainingHomeView.as_view(), name="training_home"),
    path("matrix/", TrainingMatrixView.as_view(), name="training_matrix"),
]