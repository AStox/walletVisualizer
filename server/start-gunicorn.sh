#!/bin/sh
gunicorn -b 0.0.0.0:$PORT walviz:app