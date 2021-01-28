import os
import json
import requests
from app.tasks import get_transactions
from flask import Flask, Blueprint, request, jsonify

api = Blueprint('api', __name__)

@api.route("/")
def main():
    from app.tasks import test_task
    task = test_task.delay()
    return "hi"

@api.route("/wallet/<wallet>", methods=['GET'])
def get_wallet_transactions(wallet):
    blockNumber = request.args.get("blockNumber")
    task = get_transactions.delay(wallet, blockNumber)
    return jsonify({'task_id': task.id}), 202

@api.route('/status/<task_id>', methods=['GET'])
def taskstatus(task_id):
    task = get_transactions.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)