from collections import Counter

from orbat.models import RoleSlotAssignment, SectionSlot, Role, SectionAssignment, Section


def is_section_owner(user):
    section = Section.objects.get(leader=user)

def get_section_slot_context(section):

    context = {}
    # Active role assignments for this section
    role_assignments = (
        RoleSlotAssignment.objects.filter(
            section_slot__section=section,
            end_date__isnull=True,
        ).select_related("role", "section_slot")
    )

    # Counts of active rank roles
    role_counts = Counter(a.role_id for a in role_assignments if a.role.is_rank)

    # Section slots
    section_slots = (
        SectionSlot.objects.filter(section=section)
        .select_related("user")
        .order_by("order")
    )
    slotted_ids = [slot.user.id for slot in section_slots if slot.user]

    # Preload role metadata
    all_roles = list(Role.objects.all())
    role_allowed_sections_map = {
        r.id: set(r.allowed_sections.all()) for r in all_roles
    }
    role_incompatibles_map = {
        r.id: {ir.id for ir in r.incompatible_roles.all()} for r in all_roles
    }

    # --- Roles context ---
    roles_ctx = {}
    for role in all_roles:
        print(role.name)
        if role.allowed_sections.exists() and not role.allowed_sections.contains(section):
            continue
        max_count = role.max_per_section
        current_count = role_counts.get(role.id, 0) if role.is_rank else 0
        max_reached = max_count is not None and current_count >= max_count
        allowed = not role_allowed_sections_map[role.id] or section in role_allowed_sections_map[role.id]
        has_incompatible = any(
            rid in role_incompatibles_map[role.id]
            for rid in role_counts.keys()
        )

        disabled = max_reached or not allowed or has_incompatible

        roles_ctx[role.id] = {
            "id": role.id,
            "name": role.name,
            "shorthand": role.shorthand,
            "description": role.description,
            "is_rank": role.is_rank,
            "max_count": max_count,
            "current_count": current_count,
            "disabled": disabled,
        }

    context['roles'] = roles_ctx

    # --- Section slots context ---
    slots_ctx = {}
    for slot in section_slots:
        assigned_roles = [
            a.role for a in role_assignments if a.section_slot_id == slot.id
        ]
        slots_ctx[slot.id] = {
            "id": slot.id,
            "name": slot.name,
            "colour": slot.colour if slot.colour else None,
            "user_id": slot.user.id if slot.user else None,
            "user_name": slot.user.get_ranked_name() if slot.user else None,
            "description": "", # slot.description,
            "roles": [r.id for r in assigned_roles],
        }
    context['sectionSlots'] = slots_ctx

    # --- Members context ---
    active_assignments = (
        SectionAssignment.objects.filter(section=section, end_date__isnull=True)
        .select_related("user")
    )

    members = [
        {
            "id": a.user.id,
            "name": a.user.get_ranked_name(),
            "is_assigned": a.user.id in slotted_ids
        }
        for a in active_assignments
    ]
    members_json = [
        {
            "id": str(a.user.id),
            "name": a.user.get_ranked_name(),
        }
        for a in active_assignments
    ]

    context["members"] = {m["id"]: m for m in members}
    context["members_json"] = members_json
    context["has_unallocated_members"] = any(not m["is_assigned"] for m in members)

    return context