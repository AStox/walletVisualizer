import os 

class Config(object):
    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
    BROKER_URL = os.environ.get("REDIS_URL", f'redis://{REDIS_HOST}:{REDIS_PORT}/0')
    CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", f'redis://{REDIS_HOST}:{REDIS_PORT}/0')
    WEB3_INFURA_PROJECT_ID = os.environ.get("WEB3_INFURA_PROJECT_ID")