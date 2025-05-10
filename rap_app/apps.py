# apps.py

from django.apps import AppConfig


class RapAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rap_app'


    def ready(self):
        import rap_app.signals.centres_signals
        import rap_app.signals.commentaire_signals
        import rap_app.signals.documents_signals
        import rap_app.signals.evenements_signals
        import rap_app.signals.formations_signals
        import rap_app.signals.rapports_signals
        import rap_app.signals.prospections_signals
        import rap_app.signals.prepacomp_signals
        import rap_app.signals.logs_signals  
        import rap_app.signals.statut_signals
