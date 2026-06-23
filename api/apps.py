from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        try:
            from . import cache_utils  # noqa: F401
        except Exception:
            pass
