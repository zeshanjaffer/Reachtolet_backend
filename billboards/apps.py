from django.apps import AppConfig


class BillboardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'billboards'
    
    def ready(self):
        """Import signals when app is ready"""
        import billboards.signals  # noqa