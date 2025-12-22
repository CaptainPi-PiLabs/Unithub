from django.apps import AppConfig


class OrbatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orbat'

    def ready(self):
        import orbat.signals  # noqa