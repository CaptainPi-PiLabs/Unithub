from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from apis.views.training.criterion import CriterionAPI, CriterionMoveAPI
from apis.views.training.qualification import CreateQualificationAPI, QualificationAPI, QualificationMoveAPI
from apis.views.training.trainer import TrainerAPI
from apis.views.wrapper import call_api_view


@require_POST
def create_qualification(request):
    response, success = call_api_view(
        CreateQualificationAPI,
        request,
        success_message="Qualification created successfully"
    )

    if success:
        qual_id = response.data.get("id")
        if qual_id:
            return redirect("training_qualification_detail", qual_id=qual_id)
    return redirect("training_qualification_list")

@require_POST
def save_qualification(request, qual_id):
    call_api_view(
        QualificationAPI,
        request,
        qual_id=qual_id,
        success_message="Qualification saved successfully"
    )
    return redirect("training_qualification_detail", qual_id=qual_id)

@require_POST
def remove_qualification(request, qual_id):
    request.method = "DELETE"
    response, success = call_api_view(
        QualificationAPI,
        request,
        qual_id=qual_id,
        success_message="Qualification removed successfully"
    )
    if success:
        return redirect("training_qualification_list")
    return redirect("training_qualification_detail", qual_id=qual_id)

@require_POST
def move_qualification(request, qual_id):
    call_api_view(QualificationMoveAPI, request, qual_id=qual_id)
    return redirect("training_qualification_list")

@require_POST
def save_criterion(request, qual_id):
    call_api_view(CriterionAPI, request, qual_id=qual_id)
    return redirect("training_qualification_detail", qual_id=qual_id)

@require_POST
def remove_criterion(request, qual_id):
    request.method = "DELETE"
    call_api_view(CriterionAPI, request, qual_id=qual_id)
    return redirect("training_qualification_detail", qual_id=qual_id)

@require_POST
def move_criterion(request, qual_id):
    call_api_view(CriterionMoveAPI, request, qual_id=qual_id)
    return redirect("training_qualification_detail", qual_id=qual_id)

@require_POST
def save_trainer(request, qual_id):
    call_api_view(TrainerAPI, request, qual_id=qual_id)
    return redirect("training_qualification_detail", qual_id=qual_id, tab="trainers")

@require_POST
def remove_trainer(request, qual_id):
    request.method = "DELETE"
    call_api_view(TrainerAPI, request, qual_id=qual_id)
    return redirect("training_qualification_detail", qual_id=qual_id, tab="trainers")