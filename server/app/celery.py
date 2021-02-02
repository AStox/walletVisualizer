from celery import Celery, Task
from flask import Flask


def cleanup_task_flask_context(sender: Task, **_kwargs):
    flask_context = getattr(sender.request, "flask_context", None)
    if flask_context is not None:
        flask_context.__exit__(None, None, None)


class FlaskCelery(Celery):
    app: Flask = None

    def add_task_flask_context(self, sender: Task, **_kwargs):
        if not sender.request.is_eager:
            sender.request.flask_context = self.app.app_context().__enter__()

    def init_app(self, app: Flask):
        self.app = app
        self.config_from_object(
            {'broker_url': app.config['CELERY_BROKER_URL'], 'result_backend': app.config['CELERY_RESULT_BACKEND']}
        )

        # signals.task_prerun.connect(self.add_task_flask_context)
        # signals.task_postrun.connect(cleanup_task_flask_context)

celery = FlaskCelery()
