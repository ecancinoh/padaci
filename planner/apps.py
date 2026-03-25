from django.apps import AppConfig


class PlannerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'planner'
    verbose_name = 'Planificacion Semanal'

    def ready(self):
        from . import signals  # noqa: F401
