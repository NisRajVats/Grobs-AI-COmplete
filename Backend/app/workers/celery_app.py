from app.workers.base_worker import create_celery_app

# Create Celery app instance
celery = create_celery_app()

# Celery app ready for production (remove mock for active use)
# Broker/result backend config in base_worker.get_celery_config()
