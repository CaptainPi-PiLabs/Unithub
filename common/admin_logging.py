from django.contrib.admin.models import LogEntry, ADDITION


def log_admin_addition(user, obj, message):
    LogEntry.objects.log_actions(
        user_id=user.pk,
        queryset=obj.__class__.objects.filter(pk=obj.pk),
        action_flag=ADDITION,
        change_message=message,
    )