from django.db.models import Q
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from orbat.models import SectionAssignment, SectionSlot, RoleSlotAssignment
from users.models import UserStatus, CustomUser


def update_user_section_fields(user: CustomUser):
    """Update rank + section from assignments and roles"""
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

# --- SectionAssignment ---

@receiver(pre_save, sender=SectionAssignment)
def cache_old_user_section_assignment(sender, instance, **kwargs):
    cache_old_user(instance)

@receiver([post_save, post_delete], sender=SectionAssignment)
def update_user_on_section_assignment(sender, instance, **kwargs):
    handle_user_update(instance, source="SectionAssignment")

# --- SectionSlot ---

@receiver(pre_save, sender=SectionSlot)
def cache_old_user_section_slot(sender, instance, **kwargs):
    cache_old_user(instance)

@receiver([post_save, post_delete], sender=SectionSlot)
def update_user_on_section_slot_change(sender, instance, **kwargs):
    handle_user_update(instance, source="SectionSlot")

# --- RoleSlotAssignment ---

@receiver(pre_save, sender=RoleSlotAssignment)
def cache_old_user_on_role_slot(sender, instance, **kwargs):
    if instance.pk:  # existing row
        try:
            old_instance = RoleSlotAssignment.objects.get(pk=instance.pk)
            instance._old_user = old_instance.section_slot.user if old_instance.section_slot else None
        except RoleSlotAssignment.DoesNotExist:
            instance._old_user = None

@receiver([post_save, post_delete], sender=RoleSlotAssignment)
def update_user_on_role_slot(sender, instance, **kwargs):
    section_slot = instance.section_slot
    new_user = section_slot.user if section_slot and section_slot.user else None
    handle_user_update(instance, source="RoleSlotAssignment", new_user=new_user)
