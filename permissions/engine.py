from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from apis.models import UserAPIKey, ServiceAPIKey
from orbat.models import Section
from permissions.constants import SECTION_LEADER_ACTIONS
from permissions.evaluation import check_policies
from permissions.models import PermissionGrant, PermissionRule, PermissionModule


def normalize_subject(subject):
    # Returns user, key
    if isinstance(subject, UserAPIKey):
        return subject.user, subject
    elif isinstance(subject, ServiceAPIKey):
        return None, subject
    return subject, None

def resolve_subject_filters(user=None, api_key=None):
    q = Q()
    if user:
        q |= Q(user=user)
        q |= Q(group__memberships__user=user)
    if api_key:
        if isinstance(api_key, UserAPIKey):
            q |= Q(user_api_key=api_key)
        elif isinstance(api_key, ServiceAPIKey):
            q |= Q(service_api_key=api_key)
    return q

def scope_matches(grant, content_type, obj_id, scope_key):
    # Fully global
    if grant.content_type is None and grant.object_id is None and grant.scope_key is None:
        return True

    # String scope
    if grant.scope_key is not None:
        return grant.scope_key == scope_key

    # Object / type scope
    if grant.content_type != content_type:
        return False

    if grant.object_id is None:
        return True

    return grant.object_id == obj_id

def _evaluate_grants(query, rule, content_type, object_id, scope_key):
    grants = PermissionGrant.objects.filter(rule=rule).filter(query)
    allow = None
    for grant in grants:
        if not scope_matches(grant, content_type, object_id, scope_key):
            continue
        if grant.effect == PermissionGrant.DENY:
            return False
        if grant.effect == PermissionGrant.ALLOW:
            allow = True
    return allow


def _evaluate_permissions(subject, module, action, scope):
    rule = PermissionRule.objects.filter(module=module, action=action).first()

    if not rule:
        return False

    user, api_key = normalize_subject(subject)

    ct = obj_id = scope_key = None
    if scope is not None:
        ct = ContentType.objects.get_for_model(scope)
        obj_id = getattr(scope, "id", None)
        scope_key = getattr(scope, "permission_scope_key", None)

    allow = False

    if api_key:
        key_q = resolve_subject_filters(api_key=api_key)
        result = _evaluate_grants(key_q, rule, ct, obj_id, scope_key)
        if result is False:
            return False
        if result:
            allow = True
        if not allow:
            return False

    if user:
        user_q = resolve_subject_filters(user=user)
        result = _evaluate_grants(user_q, rule, ct, obj_id, scope_key)
        if result is False:
            return False
        if result:
            allow = True

        inherited = check_policies(user, rule, scope)
        if inherited is False:
            return False
        if inherited is True:
            allow = True

    return allow


def has_permission(subject, module, action, scope=None):
    if subject is None or getattr(subject, "is_anonymous", False):
        return False

    if getattr(subject, "is_superuser", False):
        return True

    return _evaluate_permissions(subject, module, action, scope)

def has_orbat_permission(subject, action, scope=None):
    return has_permission(subject, PermissionModule.ORBAT, action, scope)

def has_training_permission(subject, action, scope=None):
    return has_permission(subject, PermissionModule.TRAINING, action, scope)

def has_any_permission(user, module, action):
    if not user or not user.is_authenticated:
        return False

    if (
        module == PermissionModule.ORBAT
        and action in SECTION_LEADER_ACTIONS
        and Section.objects.filter(leader=user).exists()
    ):
        return True

    try:
        rule = PermissionRule.objects.get(module=module, action=action)
    except PermissionRule.DoesNotExist:
        return False


    q = Q(user=user) | Q(group__memberships__user=user)

    return PermissionGrant.objects.filter(rule=rule).filter(q).exists()