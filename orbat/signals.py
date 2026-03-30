from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from orbat.models.sections import SectionSlot,  SectionSlotDetail, Section


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