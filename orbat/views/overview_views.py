from collections import defaultdict

from django.db.models import Prefetch, OuterRef, Q, Subquery
from django.shortcuts import render
from django.utils import timezone

from common.views import UnitHubTemplateView, UnitHubListView
from orbat.enums import OrbatActions
from orbat.helpers import get_section_slot_snapshots
from orbat.models.sections import SectionSlotAssignment, Section, Platoon
from orbat.views.mixins import ORBATContextMixin
from permissions.engine import has_orbat_permission
from users.models import CustomUser, UserStatus


class ORBATOverviewView(ORBATContextMixin, UnitHubTemplateView):
    template_name = "orbat/overview.html"
    breadcrumbs = [
        ("ORBAT", None),
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Build section groups with snapshots
        section_groups = []
        for section in Section.objects.order_by('platoon__order', 'order'):
            section_groups.append({
                'section': section,
                "slots": get_section_slot_snapshots(section),
            })

        # Group sections by platoon
        grouped = defaultdict(list)
        for sg in section_groups:
            platoon = sg['section'].platoon or "no_platoon"
            grouped[platoon].append(sg['section'])

        platoons = sorted(
            [p for p in grouped.keys() if p != "no_platoon"],
            key=lambda p: p.order
        )
        if "no_platoon" in grouped:
            platoons.append("no_platoon")

        assigned_user_ids = SectionSlotAssignment.objects.filter(
            end_date__isnull=True
        ).values_list('user_id', flat=True)

        remaining_users = CustomUser.objects.exclude(id__in=assigned_user_ids)

        active_deltas = remaining_users.filter(status=UserStatus.ACTIVE)
        delta_reserves = remaining_users.filter(status=UserStatus.RESERVES)
        inactive_users = remaining_users.exclude(status__in=[UserStatus.ACTIVE, UserStatus.RESERVES])

        context.update({
            'platoon_groups': platoons,
            'section_groups': section_groups,
            'active_deltas': active_deltas,
            'delta_reserves': delta_reserves,
            'inactive_users': inactive_users,
        })

        context["colour_badges"] = {
            "Gold": "bg-yellow-100 text-yellow-900 border border-yellow-300",
            "Green": "bg-green-100 text-green-900 border border-green-300",
            "Blue": "bg-blue-100 text-blue-900 border border-blue-300",
            "Red": "bg-red-100 text-red-900 border border-red-300",
        }

        return context

class ORBATSectionListView(ORBATContextMixin, UnitHubTemplateView):
    template_name = "orbat/section_list.html"
    breadcrumbs = [
        ("ORBAT", "orbat_overview"),
        ("Sections", None),
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        platoons = (
            Platoon.objects
            .order_by("order")
            .prefetch_related(
                Prefetch(
                    "sections",
                    queryset=Section.objects.order_by("order"),
                )
            )
        )

        platoon_json = {}
        for platoon in platoons:
            platoon_json[platoon.pk] = {
                "id": platoon.pk,
                "name": platoon.name,
            }

        unassigned_sections = Section.objects.filter(platoon__isnull=True).order_by("order")

        sections = Section.objects.order_by("order")
        section_json = {}
        for section in sections:
            section_json[str(section.pk)] = {
                "id": str(section.pk),
                "platoon_id": str(section.platoon.pk) if section.platoon else "",
                "platoon_name": section.platoon.name if section.platoon else "",
                "name": section.name,
                "description": section.description,
                "max_size": section.max_size,
                "shorthand": section.shorthand
            }

        context.update({
            "platoons": platoons,
            "platoons_json": platoon_json,
            "section_json": section_json,
            "unassigned_sections": unassigned_sections,
            "can_create_platoon": has_orbat_permission(user, OrbatActions.CREATE_PLATOON),
            "can_edit_platoon": has_orbat_permission(user, OrbatActions.MODIFY_PLATOON),
            "can_create_section": has_orbat_permission(user, OrbatActions.CREATE_SECTION),
        })

        return context


class ORBATMemberView(ORBATContextMixin, UnitHubListView):
    model = CustomUser
    template_name = "orbat/members.html"
    context_object_name = "members"
    breadcrumbs = [
        ("ORBAT", "orbat_overview"),
        ("Members", None)
    ]

    def get_queryset(self):
        sort = self.request.GET.get("sort", "name")
        status_filter = self.request.GET.get("status")
        today = timezone.now().date()

        current_section = (
            SectionSlotAssignment.objects
            .filter(
                user=OuterRef("pk"),
                start_date__lte=today,
            )
            .filter(
                Q(end_date__isnull=True) | Q(end_date__gte=today)
            )
            .order_by("-start_date")
            .values(
                "slot__section__name",
                "slot__section__slug"
            )[:1]
        )

        qs = CustomUser.objects.annotate(
            section_name=Subquery(current_section.values("slot__section__name")),
            section_slug=Subquery(current_section.values("slot__section__slug")),
        )

        search = self.request.GET.get("search")

        if search:
            qs = qs.filter(
                Q(display_name__icontains=search) |
                Q(username__icontains=search)
            )

        # ---- FILTERING ----
        if status_filter:
            if status_filter == "inactive":
                qs = qs.filter(is_active=False)
            if status_filter == "retired":
                qs = qs.filter(status=UserStatus.RETIRED)
            elif status_filter == "prospective":
                qs = qs.filter(status=UserStatus.APPLICANT)
            elif status_filter == "active_delta":
                qs = qs.filter(status="active", section_name__isnull=True)
            elif status_filter == "section_member":
                qs = qs.filter(section_name__isnull=False)
            elif status_filter == "delta_reserve":
                qs = qs.filter(status=UserStatus.RESERVES)
            elif status_filter == "loa":
                qs = qs.filter(status=UserStatus.LOA)
        else:
            qs = qs.filter(is_active=True)

        # ---- SORTING ----
        order_map = {
            "rank": "rank",
            "name": "display_name",
            "section": "section_name",
            "status": "status",
        }

        order_field = order_map.get(sort, "display_name")

        return qs.order_by(order_field)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("HX-Request") == "true":
            return render(
                self.request,
                "orbat/partials/members_table.html",
                context,
                **response_kwargs,
            )
        return super().render_to_response(context, **response_kwargs)