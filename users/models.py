import uuid

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import Q
from django.utils import timezone

from orbat.models import SectionAssignment, RoleSlotAssignment, SectionSlot, Section


# Create your models here.

class CustomUserManager(BaseUserManager):
    def create_user(self, display_name, username=None, email=None, password=None ,**extra_fields):
        email = self.normalize_email(email) if email else None
        user = self.model(display_name=display_name, username=username, email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, display_name, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not password:
            raise ValueError('Superuser must have a password')

        return self.create_user(display_name, username, email, password, **extra_fields)

class UserStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    LOA = 'loa', 'Leave of Absence'
    RESERVES = 'reserves', 'Reserves'
    RETIRED = 'retired', 'Retired'

class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    username = models.CharField(max_length=255, unique=True)

    display_name = models.CharField(max_length=50, unique=True)
    membership = models.CharField(max_length=20, null=True, blank=True) # Prospect, Junior Operator, Operator, Veteran
    rank = models.CharField(max_length=20, null=True, blank=True) # Private, Lance Corporal, Corporal, Sergeant
    section_name = models.CharField(max_length=50, null=True, blank=True) # Alpha, Bravo, Charlie
    callsign = models.CharField(max_length=10, null=True, blank=True) # 1-1 A, 1-5 H
    status = models.CharField(max_length=20, choices=UserStatus.choices, default=UserStatus.ACTIVE)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    timezone = models.CharField(max_length=50, default='Australia/Melbourne')

    THEME_CHOICES = [
        ('theme-light', 'Light'),
        ('theme-dark', 'Dark'),
    ]
    theme = models.CharField(
        max_length=15,
        choices=THEME_CHOICES,
        default='theme-light',
        help_text="User interface theme preference"
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'id'
    REQUIRED_FIELDS = ['display_name', 'username']

    class Meta:
        ordering = ('display_name',)
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.get_name_with_callsign()

    def get_ranked_name(self):
        if self.rank:
            return f"{self.rank} {self.display_name}"
        return self.display_name

    def get_name_with_callsign(self):
        if self.callsign:
            return f"[{self.callsign}] - {self.get_ranked_name()}"
        return self.get_ranked_name()

    def get_section(self):
        assignment = SectionAssignment.objects.filter(
            Q(user=self) | Q(end_date__isnull=True) | Q(end_date__gt=timezone.now())
        ).first()
        if assignment:
            return assignment.section
        return None

    def has_permission(self, permission, module, scope=None):
        from permissions.services import user_has_permission
        return user_has_permission(self, permission, module, scope)

    def save(self, *args, **kwargs):
        if self.status == UserStatus.RETIRED:
            self.rank = None
            self.section = None
        else:
            # If no rank set and not retired → default to PVT
            if not self.rank:
                self.rank = "PVT"
        super().save(*args, **kwargs)