from django.apps import AppConfig


class ArtworkConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'artwork'

    def ready(self):
        """Import signals when app is ready."""
        import artwork.signals  # noqa: F401
