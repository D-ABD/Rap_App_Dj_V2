# apps.py

from django.apps import AppConfig


class RapAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rap_app'


    def ready(self):
        import rap_app.signals.commentaire_signals
        import rap_app.signals.documents_signals
        import rap_app.signals.evenements_signals
