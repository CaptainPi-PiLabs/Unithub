import re
import uuid

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


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

class UnitMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.display_name} ({self.date_range_display()})"

    def date_range_display(self):
        end_text = self.end_date or "Current"
        return f"{self.start_date} - {end_text}"

    @classmethod
    def get_for_user(cls, user):
        return cls.objects.filter(user=user).order_by('-start_date')

    @classmethod
    def get_current_for_user(cls, user):
        return cls.objects.filter(user=user, end_date__isnull=True).first()

class MembershipRanks(models.TextChoices):
    JUNIOR_OPERATOR = 'junior', 'Junior Operator'
    OPERATOR = 'operator', 'Operator'
    VETERAN = 'veteran', 'Veteran'

class MembershipPromotions(models.Model):
    membership = models.ForeignKey(UnitMembership, on_delete=models.CASCADE, related_name="promotions")
    rank = models.CharField(max_length=20, choices=MembershipRanks.choices)
    date_awarded = models.DateField()

    class Meta:
        ordering = ["date_awarded"]
        verbose_name_plural = "Membership Promotions"
        constraints = [
            models.UniqueConstraint(
                fields=["membership", "rank"],
                name="unique_rank_per_membership"
            )
        ]

    def __str__(self):
        return f"{self.membership.user} - {self.get_rank_display()}"

    def clean(self):
        if self.date_awarded < self.membership.start_date:
            raise ValidationError("Promotion date cannot be before membership start.")

        if self.membership.end_date and self.date_awarded > self.membership.end_date:
            raise ValidationError("Promotion date cannot be after membership end.")


class UserStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    APPLICANT = 'applicant', 'Applicant'
    LOA = 'loa', 'Leave of Absence'
    RESERVES = 'reserves', 'Reserves'
    RETIRED = 'retired', 'Retired'

class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    username = models.CharField(max_length=255, unique=True)

    display_name = models.CharField(max_length=50, unique=True)
    membership = models.CharField(max_length=20, null=True, blank=True) # Prospect, Junior Operator, Operator, Veteran # TODO Remove
    rank = models.CharField(max_length=20, null=True, blank=True) # Private, Lance Corporal, Corporal, Sergeant
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

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['display_name']

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

    def get_current_membership_display(self):
        membership = UnitMembership.get_current_for_user(self)
        if not membership:
            return "-"

        promotion = membership.promotions.order_by('-date_awarded').first()
        if promotion:
            return promotion.get_rank_display()

        return "Prospective"

    def get_name_with_callsign(self):
        return self.get_ranked_name()

    def get_section(self, date=None):
        from orbat.helpers import get_section_for_user
        return get_section_for_user(self, date)

    def save(self, *args, **kwargs):
        if self.status == UserStatus.RETIRED or self.status == UserStatus.APPLICANT:
            self.rank = None
        else:
            # If no rank set and not retired → default to PVT
            if not self.rank:
                self.rank = "PVT"
        super().save(*args, **kwargs)

    def change_status(self, new_status, actioned_by=None, reason=None):
        old_status = self.status
        if old_status == new_status:
            return

        self.status = new_status
        self.save(update_fields=["status"])

        self._log_status_transition(old_status, new_status, actioned_by, reason)

    @staticmethod
    def normalize_username(name):
        return re.sub(r"[^a-z0-9]", "", name.lower())