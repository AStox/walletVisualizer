import os 

class Config(object):
    REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
    REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", f'redis://{REDIS_HOST}:{REDIS_PORT}/0')
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", f'redis://{REDIS_HOST}:{REDIS_PORT}/0')