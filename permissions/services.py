import logging

from django.contrib.contenttypes.models import ContentType

from permissions.contrants import INHERITED_RULES, PERMISSIONS
from permissions.models import PermissionGrant


logger = logging.getLogger(__name__)

def permission_matches(grant_permission, requested_permission):
    """Match permission string with wildcard support."""
    return grant_permission == "*" or grant_permission == requested_permission

def check_inherited_permissions(user, permission, module, scope):
    for rule in INHERITED_RULES:
        if rule["module"] != module:
            continue
        if permission not in rule["permissions"]:
            continue
        if rule["check"](user, scope):
            return True
    return False

def normalize_scope(scope):
    """
    Returns (content_type, object_id, scope_key)
    Exactly one of:
      - content_type/object_id (object or type-level)
      - scope_key (string scope)
    """
    if scope is None:
        return None, None, None

    if hasattr(scope, "_meta"):  # model instance
        ct = ContentType.objects.get_for_model(scope)
        return ct, scope.id, None

    if isinstance(scope, str):
        return None, None, scope

    raise TypeError(f"Unsupported scope type: {type(scope)}")

def user_has_permission(user, permission, module, scope=None):
    """
    Check if the user has permission for a given module/action, optionally scoped to an object or a type string.
    scope = None (global) or an instance
    """
    module_perms = PERMISSIONS.get(module, {})
    if permission not in module_perms:
        logger.debug(
            f"Permission check requested with unknown permission: "
            f"{module}.{permission} (user={user})"
        )

    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    ct, obj_id, scope_key = normalize_scope(scope)

    grants = PermissionGrant.objects.filter(
        group__memberships__user=user,
        module=module,
    )

    allow = False
    for grant in grants:
        # Object match logic
        if grant.content_type is None and grant.object_id is None and grant.scope_key is None:
            obj_match = True  # fully global
        elif grant.scope_key and grant.scope_key == scope_key:
            obj_match = True  # string scope match
        elif ct == grant.content_type:
            if grant.object_id is None:
                obj_match = True  # type-level
            elif obj_id == grant.object_id:
                obj_match = True  # object-level
            else:
                obj_match = False
        else:
            obj_match = False

        if not obj_match:
            continue

        # Action match
        if not permission_matches(grant.permission, permission):
            continue

        # Deny overrides
        if grant.effect == PermissionGrant.DENY:
            return False

        if grant.effect == PermissionGrant.ALLOW:
            allow = True

    allow = allow or check_inherited_permissions(user, permission, module, scope)

    return allow