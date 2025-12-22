from collections import defaultdict

from django.db.models import Q, Value, When, Case, F
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone

from orbat.models import SectionAssignment, Section, SectionSlot
from orbat.views.orbat_base_views import ORBATBaseView
from users.models import CustomUser, UserStatus


class ORBATOverviewView(ORBATBaseView):
    template_name = "orbat_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"name": "ORBAT", "url": None},
        ]
        # 1. Users in sections
        now = timezone.now()

        active_assignments = SectionAssignment.objects.filter(
            Q(end_date__isnull=True) | Q(end_date__gt=now)
        ).select_related("user", "section")

        grouped = defaultdict(list)
        section_groups = []
        for section in Section.objects.order_by('platoon__order', 'order'):
            if active_assignments.filter(section=section).exists():
                section_slots = (SectionSlot.objects.filter(section=section).select_related('user').order_by('order'))
                section_assignments = []
                for slot in section_slots:
                    if slot.user and active_assignments.filter(user=slot.user, section=section).exists():
                        section_assignments.append({
                            "sectionSlot": slot.name,
                            "user": slot.user,
                        })
                slotted_users = {slot.user_id for slot in section_slots if slot.user}
                for assignment in active_assignments.filter(section=section).select_related('user'):
                    if assignment.user_id not in slotted_users:
                        section_assignments.append({
                            "sectionSlot": "",
                            "user": assignment.user,
                        })

                section_groups.append({
                    'section': section,
                    "assignments": section_assignments,
                })
                platoon = section.platoon or "no_platoon"
                grouped[platoon].append(section)

        platoons = sorted(
            [platoon for platoon in grouped.keys() if platoon != "no_platoon"],
            key=lambda platoon: platoon.order
        )
        if "no_platoon" in grouped:
            platoons.append("no_platoon")

        assigned_user_ids = active_assignments.values_list("user_id", flat=True)
        remaining_users = CustomUser.objects.exclude(id__in=assigned_user_ids)

        active_deltas = remaining_users.filter(status=UserStatus.ACTIVE)
        delta_reserves = remaining_users.filter(status=UserStatus.RESERVES)
        inactive = remaining_users.exclude(status__in=[UserStatus.ACTIVE, UserStatus.RESERVES])

        context.update({
            'platoon_groups': platoons,
            'section_groups': section_groups,
            'active_deltas': active_deltas,
            'delta_reserves': delta_reserves,
            'inactive_users': inactive,
        })

        return context

class ORBATMemberView(ORBATBaseView):
    template_name = "orbat_members.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"name": "ORBAT", "url": 'orbat_overview'},
            {"name": "Members", "url": None},
        ]

        sort = self.request.GET.get("sort", "name")
        order_map = {
            "rank": "rank",
            "name": "display_name",
            "section": "section_name",
        }

        order_field = order_map.get(sort, "display_name")

        members = CustomUser.objects.all().order_by(order_field)
        context['members'] = members
        print("Calling context for member view")

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("HX-Request") == "true":
            print("Calling sub table for members")
            return render(self.request, "partials/members_table.html", context, **response_kwargs)
        return super().render_to_response(context, **response_kwargs)