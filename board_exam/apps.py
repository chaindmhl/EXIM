from django.apps import AppConfig

class BoardExamConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'board_exam'

    def ready(self):
        from .firebase import initialize_firebase
        initialize_firebase()