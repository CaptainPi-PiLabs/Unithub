from datetime import timedelta

from django import template
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from timeline.models import TimelineEntry, TimelineTypes
from timeline.utils import get_timeline_entries, get_recent_training_timeline, build_timeline_context, \
    group_timeline_entries, get_active_context, get_user_query, get_start_date_query, get_section_query


register = template.Library()

def get_object_link(obj):
    if hasattr(obj, 'get_absolute_url'):
        return format_html('<a href="{}">{}</a>', obj.get_absolute_url(), str(obj))

    # Fallback: use the admin change page if object has a ContentType
    try:
        ct = ContentType.objects.get_for_model(obj.__class__)
        url = reverse(
            f"admin:{ct.app_label}_{ct.model}_change",
            args=[obj.pk],
        )
        return format_html('<a href="{}">{}</a>', url, str(obj))
    except Exception:
        return str(obj)


@register.filter
def timeline_label(entry: TimelineEntry):
    if entry.type == TimelineTypes.UNIT_JOINED:
        return f"{entry.user} joined the unit"

    if entry.type == TimelineTypes.UNIT_LEFT:
        return f"{entry.user} left the unit"

    return str(entry)

@register.filter
def underscore_to_space(value):
    """Replace underscores with spaces."""
    return str(value).replace("_", " ")

@register.inclusion_tag("timeline_list.html", takes_context=True)
def render_orbat_timeline(context, user_qs=None, section=None):
    request = context.get("request")

    context = {}

    active_context = get_active_context(request)
    user_query = get_user_query(user_qs, active_context["active_timeline_user"])
    section_query = get_section_query(section, active_context["active_timeline_section"])
    default_date_range = timezone.now() - timedelta(days=90)
    default_date_range = None
    start_date_query = get_start_date_query(default_date_range, active_context["active_timeline_range"])

    entries = get_timeline_entries(
        user_qs=user_query,
        section=section_query,
        start_date=start_date_query,
        exclude_types=[TimelineTypes.TRAINING_COMPLETED],
    )

    context.update(active_context)
    context.update(build_timeline_context(entries))
    context["entries"] = group_timeline_entries(entries)
    return context

@register.inclusion_tag("timeline_list.html", takes_context=True)
def render_training_timeline(context, user_qs=None, section=None):

    active_context = get_active_context(context)
    active_user = active_context.get("active_timeline_user")
    if active_user:
        User = get_user_model()
        active_user = User.objects.get(id=active_user)
    else:
        active_user = user_qs
    active_section = active_context.get("active_timeline_section")
    if active_section:
        from orbat.models import Section
        active_section = Section.objects.get(id=active_section)
    else:
        active_section = section

    entries = get_recent_training_timeline(user_qs=active_user, section=active_section)
    context = build_timeline_context(entries)
    context.update(get_active_context(context))
    context["entries"] = group_timeline_entries(entries)
    return context

@register.inclusion_tag("timeline_list.html")
def render_timeline(user_qs=None, section=None, start_date=None, end_date=None):
    User = get_user_model()
    if user_qs is None:
        user_qs = User.objects.all()
    elif isinstance(user_qs, User):
        user_qs = User.objects.filter(pk=user_qs.pk)
    elif isinstance(user_qs, list):
        user_qs = User.objects.filter(pk__in=[u.pk for u in user_qs])
    entries = get_timeline_entries(user_qs, section, start_date, end_date)
    return {"entries": group_timeline_entries(entries)}