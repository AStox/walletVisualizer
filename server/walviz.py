from app import celery, create_app

app = create_app()
celery = celery