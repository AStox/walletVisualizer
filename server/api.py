import requests
import os
import time
import json
import functools
from flask import Flask, request, jsonify, url_for
from functools import reduce
from web3 import exceptions
from web3.auto.infura import w3

from app import app
from tasks import get_transactions

my_account = os.environ.get("MY_ACC")
etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")

special_contracts = json.load(open("contracts.json", "r"))

errors = []

@app.route("/")
def main():
    return "hi"

@app.route("/wallet/<wallet>")
def get_wallet_transactions(wallet):
    blockNumber = request.args.get("blockNumber")
    task = get_transactions.delay(wallet, blockNumber)
    return jsonify({'task_id': task.id}), 202

@app.route('/status/<task_id>')
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