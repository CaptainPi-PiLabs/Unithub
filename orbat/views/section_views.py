from core.views import UnitHubDetailView, UnitHubListView, UnitHubUpdateView
from orbat.enums import OrbatActions
from orbat.models import Section
from orbat.utils import get_section_slot_context
from orbat.views import ORBATContextMixin
from permissions.models import PermissionModule
from permissions.engine import has_permission


class ORBATSectionDetailView(ORBATContextMixin, UnitHubDetailView):
    model = Section
    template_name = 'orbat_section_detail.html'
    slug_field = 'name'
    slug_url_kwarg = 'section_name'
    context_object_name = 'section'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section = self.object
        user = self.request.user

        context["breadcrumbs"] = [
            {"name": "ORBAT", "url": "/orbat/"},
            {"name": "Sections", "url": "/orbat/"},
            {"name": section.name, "url": None},
        ]
        context["can_manage"] = has_permission(user, PermissionModule.ORBAT, OrbatActions.MODIFY_SECTION, section)
        context.update(get_section_slot_context(section))
        return context

class ORBATSectionHistoryView(ORBATContextMixin, UnitHubListView):
    pass

class ORBATSectionEditView(ORBATContextMixin, UnitHubUpdateView):
    pass