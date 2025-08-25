"""
This file contains the application configuration for the 'store' app.
It's used to configure app-specific attributes. We use the 'ready()' method
here to import our signals.py file, ensuring that our signal handlers are
connected and ready to fire when the application starts.
"""
from django.apps import AppConfig

class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    # This is a special method that Django runs once the application is fully loaded.
    def ready(self):
        # By importing our signals file here, we are effectively "turning on"
        # our signal receivers (the smoke detectors), making them ready to listen for events.
        import store.signals