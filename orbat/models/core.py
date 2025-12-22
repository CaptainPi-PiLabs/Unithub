from django.conf import settings
from django.db import models, transaction
from django.db.models import Max
from django.utils import timezone

from external_auth.models import DiscordAccount
from unithub.mixins.model_mixin import OrderedModelMixin


class Platoon(OrderedModelMixin, models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Section(OrderedModelMixin, models.Model):
    name = models.CharField(max_length=50, unique=True)
    shorthand = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20)
    max_size = models.IntegerField()
    platoon = models.ForeignKey(Platoon, null=True, blank=True, related_name='subsections', on_delete=models.SET_NULL)
    leader = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='leads_section', on_delete=models.SET_NULL)

    _order_scope_fields = ["platoon"]
    class Meta:
        ordering = ["platoon", "order"]

    def __str__(self):
        return self.name

    def can_manage(self, user):
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or self.leader == user


class Role(models.Model):
    name = models.CharField(max_length=50)
    shorthand = models.CharField(max_length=10)

    description = models.TextField(blank=True)
    max_per_section = models.PositiveIntegerField(null=True, blank=True)
    allowed_sections = models.ManyToManyField(Section, blank=True)
    is_rank = models.BooleanField(default=False)
    incompatible_roles = models.ManyToManyField('self', symmetrical=True, blank=True)

    def __str__(self):
        return self.name

class SectionAssignment(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.end_date:
            return f"{self.user} - {self.section.name} - Expired"
        return f"{self.user} - {self.section.name}"

    def is_active(self):
        return not self.end_date or self.end_date >= timezone.now().date()

class SectionSlot(OrderedModelMixin, models.Model):
    name = models.CharField(max_length=50)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    COLOUR_CHOICES = [
        ("Gold", "Gold"),
        ("Green", "Green"),
        ("Red", "Red"),
        ("Blue", "Blue"),
    ]
    colour = models.CharField(max_length=10, null=True, blank=True, choices=COLOUR_CHOICES)
    _order_scope_fields = ["section"]

    class Meta:
        ordering = ['section', 'order']

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.user:
                SectionSlot.objects.filter(section=self.section, user=self.user).exclude(pk=self.pk).update(user=None)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.section} - {self.name}"


class RoleSlotAssignment(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    section_slot = models.ForeignKey(SectionSlot, on_delete=models.CASCADE)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.section_slot} - {self.role}"

    def is_active(self):
        return not self.end_date or self.end_date >= timezone.now().date()

class Applications(models.Model):
    date = models.DateTimeField(default=timezone.now)
    processed_date = models.DateTimeField(null=True, blank=True)
    actioned_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="%(class)s_actioned")
    denied = models.BooleanField(default=False)

    class Meta:
        abstract = True

class UnitApplication(Applications):
    STATUS_CHOICES = [
        ("unclaimed", "Unclaimed"),
        ("waiting_reply", "Waiting reply"),
        ("bct_planned", "BCT planned"),
        ("passed", "Passed"),
        ("denied", "Denied"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="unit_application")
    external_account = models.OneToOneField(DiscordAccount, on_delete=models.CASCADE)
    teamspeak_id = models.PositiveIntegerField(null=True, blank=True)
    over_18 = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="unclaimed")

    def __str__(self):
        return self.external_account.username

class SectionApplication(Applications):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="section_applications")
    section_slot = models.ForeignKey(SectionSlot, on_delete=models.CASCADE)