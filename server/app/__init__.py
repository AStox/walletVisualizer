import os
from flask import Flask
from config import Config
from celery import Celery
from redis import StrictRedis
# from werkzeug.middleware.proxy_fix import ProxyFix

def create_app(config_class=Config()):
    app = Flask(__name__)
    # app.wsgi_app = ProxyFix(
    #     app.wsgi_app, x_for=1, x_host=1, x_port=1, x_prefix=1, x_proto=1
    # )
    app.config.from_object(config_class)
    app.logger.info("Application created.")

    global redis
    redis = StrictRedis(
        host=config_class.REDIS_HOST, port=config_class.REDIS_PORT
    )

    app.logger.info("Registering views")
    # for view_name in importlib.import_module("app.views").__all__:
    #     if view_name is not None:
    #         view = importlib.import_module(f"app.views.{view_name}")
    #         app.register_blueprint(view.mod)
    from app.views.api import api
    app.register_blueprint(api, url_prefix='/api')
    # Celery tasks
    app.logger.info("Registering tasks")

    # import app.tasks as _

    app.logger.info("Initializing Celery")
    

    app.logger.info("Registering schemas")
    # import app.schemas as _

    return app

app = create_app()
celery = Celery(app.name, broker='redis://redis:6379/0', backend='redis://redis:6379/0',)
celery.conf.update(app.config)