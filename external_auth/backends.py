from django.contrib.auth.backends import BaseBackend


class ExternalAccountBackend(BaseBackend):
    """
    Authenticate using an ExternalAccount (DiscordAccount/SteamAccount).
    """
    def authenticate(self, request, external_account=None, **kwargs):
        if external_account is None:
            return None
        # Only authenticate if user is linked and active
        user = getattr(external_account, "user", None)
        if user and user.is_active:
            return user
        return None

    def get_user(self, user_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None