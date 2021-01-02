import logging
import sys
from tasks import celery
celery.start(argv=["celery", "-A", "worker", "-l", "info"])