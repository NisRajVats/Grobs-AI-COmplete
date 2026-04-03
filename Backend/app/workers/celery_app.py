from app.workers.base_worker import create_celery_app

# Create Celery app instance
celery = create_celery_app()

# If celery is not available, we should provide a mock for it to avoid errors during import
if celery is None:
    class MockCelery:
        def task(self, *args, **kwargs):
            return lambda f: f
    celery = MockCelery()
