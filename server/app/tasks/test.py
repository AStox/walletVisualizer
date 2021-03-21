from app import celery

@celery.task(bind=True)
def test_task(self):
    pass