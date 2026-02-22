from django.contrib.contenttypes.models import ContentType
from dataclasses import dataclass
from typing import Optional
from django.utils import timezone

from orbat.enums import OrbatActions
from orbat.models.sections import SectionSlotAssignment, SectionSlot, SectionApplication, Section
from orbat.selectors import get_section_slot
from permissions.engine import has_orbat_permission, has_any_permission
from permissions.models import PermissionGrant, PermissionRule, PermissionModule, PermissionGroupMembership


@dataclass(frozen=True)
class SectionSlotSnapshot:
    slot: "SectionSlot"
    section: "Section"

    id: int
    name: str
    colour: Optional[str]
    is_leader: bool
    is_officer: bool

    user: Optional["User"]
    assignment: Optional["SectionSlotAssignment"]
    details: Optional["SectionSlotDetail"]

    date: timezone.datetime

    @property
    def is_vacant(self) -> bool:
        return self.user is None

    @property
    def display_name(self) -> str:
        return f"{self.section} – {self.name}"

    def can_request(self, user) -> bool:
        if self.is_vacant:
            return True
        return False  # expand later if you support swap logic

def get_section_slot_snapshots(section, date=None):
    """
    Returns an ordered list of SectionSlotSnapshot objects
    representing the ORBAT state at the given date.
    """
    if date is None:
        date = timezone.now().date()

    slots = (
        section.slots
        .select_related("section")
        .all()
    )

    snapshots = []

    for slot in slots:
        details = slot.get_details_at(date)
        assignment = slot.get_assignment_at(date)

        if not details:
            continue

        snapshots.append(
            SectionSlotSnapshot(
                slot=slot,
                id=slot.id,
                section=section,
                name=details.name,
                colour=details.colour,
                is_leader=slot.is_leader,
                is_officer=details.is_officer,
                user=assignment.user if assignment else None,
                assignment=assignment,
                details=details,
                date=date,
            )
        )

    return sorted(snapshots, key=_slot_snapshot_sort_key)


TEAM_ORDER = {
    "Gold": 1,
    "Green": 2,
    "Red": 3,
    "Blue": 4,
    None: 5,
}

def _slot_snapshot_sort_key(snapshot: SectionSlotSnapshot):
    """
    Ordering rules:
    - Leaders first
    - Officers before non-officers
    - Team order: Gold, Green, Red, Blue
    - Name as tie-breaker
    """
    return (
        not snapshot.is_leader,                      # leaders first
        not snapshot.is_officer,                     # officers first
        TEAM_ORDER.get(snapshot.colour, 99),
        snapshot.name.lower(),
    )

def get_section_for_user(user, date=None):
    slot = get_section_slot(user, date)
    return slot.section if slot else None

def get_accessible_section_applications(user):
    if not user or not user.is_authenticated:
        return SectionApplication.objects.none()

    # Early global permission check
    if has_orbat_permission(user, OrbatActions.VIEW_SECTION_APPLICATIONS):
        return SectionApplication.objects.filter(closed=False)

    qs = SectionApplication.objects.none()

    slot = get_section_slot(user)
    if slot and slot.is_officer():
        qs |= SectionApplication.objects.filter(section=slot.section, closed=False)
        user_section_id = slot.section.id
    else:
        user_section_id = None

    if not has_any_permission(user, PermissionModule.ORBAT, OrbatActions.VIEW_SECTION_APPLICATIONS):
        return qs


    rule = PermissionRule.objects.filter(
        module=PermissionModule.ORBAT,
        action=OrbatActions.VIEW_SECTION_APPLICATIONS
    ).first()

    if rule:
        ct = ContentType.objects.get_for_model(Section)

        # User grants
        user_grants = PermissionGrant.objects.filter(rule=rule, content_type=ct, user=user).exclude(
            object_id=user_section_id)
        qs |= SectionApplication.objects.filter(section_id__in=user_grants.values_list("object_id", flat=True),
                                                closed=False)

        # Group grants
        group_ids = PermissionGroupMembership.objects.filter(user=user).values_list("group_id", flat=True)
        group_grants = PermissionGrant.objects.filter(rule=rule, content_type=ct, group_id__in=group_ids).exclude(
            object_id=user_section_id)
        qs |= SectionApplication.objects.filter(section_id__in=group_grants.values_list("object_id", flat=True),
                                                closed=False)

    return qs.distinct()