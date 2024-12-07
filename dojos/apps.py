from django.apps import AppConfig


class DojosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dojos'

    def ready(self):
        import dojos.signals