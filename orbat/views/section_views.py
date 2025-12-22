import json

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View

from orbat.models import get_section_on_date, SectionSlot, Section, SectionAssignment
from orbat.utils import get_section_slot_context
from orbat.views import ORBATBaseView


class ORBATSectionDetailView(ORBATBaseView):
    template_name = 'orbat_section_detail.html'

    def dispatch(self, request, *args, **kwargs):
        section_name = self.kwargs.get('section_name')
        try:
            self.section_obj = Section.objects.get(name=section_name)
        except ObjectDoesNotExist:
            messages.error(self.request, f'Section {section_name} not found')
            return redirect("/orbat")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["breadcrumbs"] = [
            {"name": "ORBAT", "url": "/orbat/"},
            {"name": "Sections", "url": "/orbat/"},
            {"name": self.section_obj.name, "url": None},
        ]
        context["section"] = self.section_obj
        context["can_manage"] = self.section_obj.can_manage(user)
        section_context = get_section_slot_context(self.section_obj)
        context.update(section_context)
        return context

class ORBATSectionHistoryView(ORBATBaseView):
    pass

class ORBATSectionEditView(ORBATBaseView):
    pass