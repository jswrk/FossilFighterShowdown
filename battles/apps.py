from django.apps import AppConfig


class BattlesConfig(AppConfig):
    name = 'battles'

    def ready(self):
        import battles.signals  # noqa: F401
