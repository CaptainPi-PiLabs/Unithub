def allow_anonymous(obj):
    # Supports both function and class based views
    setattr(obj, "is_public", True)
    return obj