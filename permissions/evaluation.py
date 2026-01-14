from permissions.policies import POLICIES


def check_policies(user, rule, scope):
    """
    Evaluate policy-based permissions.

    Returns:
    - True  -> allow
    - False -> deny
    - None  -> no policy matched
    """
    allow = None

    for policy in POLICIES:
        result = policy.applies(user, rule, scope)
        if result is not None:
            if result:
                allow = True
            else:
                return False
    return allow