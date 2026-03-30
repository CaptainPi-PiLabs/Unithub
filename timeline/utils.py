from collections import defaultdict
from datetime import timedelta, datetime
from uuid import UUID

from django.contrib.auth import get_user_model
from django.utils import timezone

from orbat.models.sections import Section


def build_timeline_context(timeline_qs):
    """
    Build context for timeline filters: available users, sections, and date ranges.
    Returns a dict to merge into the template context.
    """
    # Unique users and sections from the timeline queryset
    timeline_qs = timeline_qs.select_related('user', 'section')
    users = sorted({entry.user for entry in timeline_qs}, key=lambda u: getattr(u, 'display_name', str(u)))
    sections = sorted({entry.section for entry in timeline_qs if entry.section}, key=lambda s: s.name)

    context = {}

    if len(users) > 1:
        context["timeline_scope_users"] = users
    if len(sections) > 1:
        context["timeline_scope_sections"] = sections

    # Date range buttons
    now = timezone.now().date()
    context['timeline_scope_ranges'] = [
        ('last_week', now - timedelta(days=7)),
        ('last_month', now - timedelta(days=30)),
        ('last_3_months', now - timedelta(days=90)),
        ('last_6_months', now - timedelta(days=180)),
        ('last_year', now - timedelta(days=365)),
    ]

    return context

def group_timeline_entries(entries_qs):
    entries_qs = entries_qs.select_related('user', 'section').order_by('-timestamp')

    grouped = defaultdict(list)
    for entry in entries_qs.order_by('-timestamp'):
        grouped[entry.timestamp.date()].append(entry)

    # sorted by date descending
    return sorted(grouped.items(), key=lambda x: x[0], reverse=True)

def get_active_context(request):
    active_user = request.GET.get("timeline_user") if request else None
    active_section = request.GET.get("timeline_section") if request else None
    active_range = request.GET.get("timeline_range") if request else None

    return {
        "active_timeline_user": active_user,
        "active_timeline_section": active_section,
        "active_timeline_range": active_range,
    }

def get_user_query(user_qs, active_timeline_user=None):
    User = get_user_model()

    # If an active user is set via the query param
    if active_timeline_user:
        return User.objects.filter(pk=active_timeline_user)

    # If a single User instance
    if isinstance(user_qs, User):
        return User.objects.filter(pk=user_qs.pk)

    # If a single UUID
    if isinstance(user_qs, UUID) or isinstance(user_qs, str):
        return User.objects.filter(pk=user_qs)

    # If None, return all users
    if user_qs is None:

        return User.objects.all()

    # If it's already a queryset or iterable of PKs
    try:
        # If it's a queryset, return as-is
        if hasattr(user_qs, "exists"):
            return user_qs
        # If it's an iterable of UUIDs/PKs, wrap in queryset
        return User.objects.filter(pk__in=list(user_qs))
    except Exception:
        # Fallback to all users
        return User.objects.all()


def get_section_query(section_qs, active_timeline_section=None):
    if not active_timeline_section:
        return section_qs
    return Section.objects.filter(pk=active_timeline_section).first()

def get_start_date_query(default_start, range_str):
    if not range_str:
        return default_start

    try:
        # Parse string to date
        dt = datetime.strptime(range_str, "%Y-%m-%d")
        # Make timezone-aware
        return timezone.make_aware(datetime.combine(dt, datetime.min.time()))
    except ValueError:
        # If parsing fails, fallback to default
        return default_start