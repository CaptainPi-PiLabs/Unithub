from django.db.models import Q
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from orbat.models.sections import SectionSlot, SectionSlotAssignment, SectionSlotDetail, Section
from timeline.models import TimelineTypes
from timeline.utils import add_entry
from users.models import UserStatus, CustomUser


@receiver(post_save, sender=Section)
def create_section_leader_slot(sender, instance, created, **kwargs):
    if not created:
        return

    leader_slot = SectionSlot.objects.create(
        section=instance,
        is_leader=True,
    )

    SectionSlotDetail.objects.create(
        slot=leader_slot,
        name="Section Leader",
        colour="Gold",
        is_officer=True,
        start_date=timezone.now().date(),
    )

def update_user_section_fields(user: CustomUser):
    """Update rank + section from assignments and roles"""

    """
    if user.status == UserStatus.RETIRED:
        user.rank = None
        user.section_name = None
    else:
        assignment = SectionAssignment.objects.filter(
            user=user,
            end_date__isnull=True
        ).first()
        user.rank = "PVT"
        if assignment and assignment.section:
            user.section_name = assignment.section.name
            section_slot = SectionSlot.objects.filter(
                section=assignment.section,
                user=user
            ).first()
            if section_slot:
                role_assignment = RoleSlotAssignment.objects.filter(
                    section_slot=section_slot,
                    role__is_rank=True,
                ).filter(
                    Q(end_date__isnull=True) | Q(end_date__gt=timezone.now())
                ).select_related("role").first()
                if role_assignment:
                    user.rank = role_assignment.role.shorthand
        else:
            user.section_name = None
    user.save(update_fields=["rank", "section_name"])
    """

def cache_old_user(instance):
    if instance.pk:
        Model = type(instance)
        try:
            old_instance = Model.objects.get(pk=instance.pk)
            instance._old_user = old_instance.user if old_instance else None
        except Model.DoesNotExist:
            instance._old_user = None
    else:
        instance._old_user = None


def log_assignment_change(user, action, source, obj):
    pass


def handle_user_update(instance, source=None, new_user=None):
    new_user = new_user if new_user is not None else getattr(instance, "user", None)
    old_user = getattr(instance, "_old_user", None)

    if old_user and old_user != new_user:
        update_user_section_fields(old_user)
        if source:
            log_assignment_change(user=old_user, action="removed", source=source, obj=instance)
    if new_user:
        update_user_section_fields(new_user)
        if source:
            log_assignment_change(user=new_user, action="added", source=source, obj=instance)

# --- SectionSlotAssignment ---

@receiver(pre_save, sender=SectionSlotAssignment)
def cache_old_user_section_assignment(sender, instance, **kwargs):
    cache_old_user(instance)

@receiver(post_save, sender=SectionSlotAssignment)
def handle_assignment_created(sender, instance, created, **kwargs):
    if not created:
        return

    section = instance.slot.section

    # Additionally log section join if applicable
    if getattr(instance, "_is_new_section_join", False):
        add_entry(
            TimelineTypes.SECTION_JOINED,
            user=instance.user,
            section=section,
            related_object=instance,
        )

    # Always log role assignment
    add_entry(
        TimelineTypes.ROLE_ASSIGNED,
        user=instance.user,
        section=section,
        snapshot_name=instance.slot.get_name(),
        related_object=instance,
    )

@receiver(post_save, sender=SectionSlotAssignment)
def handle_assignment_end(sender, instance, created, **kwargs):
    if created:
        return

    old = getattr(instance, "_old", None)
    if not old:
        return

    if old.end_date is None and instance.end_date is not None:
        add_entry(
            TimelineTypes.SECTION_LEFT,
            user=instance.user,
            section=instance.slot.section,
            related_object=instance,
        )

@receiver(post_delete, sender=SectionSlotAssignment)
def log_section_assignment_delete(sender, instance, **kwargs):
    log_assignment_change(
        user=instance.user,
        action="removed",
        source="SectionSlotAssignment",
        obj=instance,
    )