#!/usr/bin/env python
import click
import os

from app import create_app


@click.group()
def cli():
    pass


@cli.command()
@click.option("-h", "--host", default="127.0.0.1", help="Bind the server to host HOST")
@click.option("-p", "--port", default=5000, help="Bind the server to port PORT")
def serve(host, port):
    """
    Runs the Flask development server.
    """
    os.environ["REDIS_HOST"] = host
    app = create_app()
    app.run(host=host, port=port, debug=True, threaded=True)


@cli.command()
def worker():
    """
    Runs a Celery worker.
    """
    from walviz import celery

    celery.start(argv=["celery", "worker"])


if __name__ == "__main__":
    cli()
