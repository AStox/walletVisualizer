import time
import requests
import os
from flask import Flask

app = Flask(__name__)

my_account = os.environ.get("MY_ACC")
etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")


@app.route("/")
def main():
    return "hi"


@app.route("/wallet/<wallet>")
def get_transactions(wallet):
    response = requests.get(
        f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet}&startblock=0&endblock=99999999&sort=asc&apikey={etherscan_api_key}"
    )
    transactions = response.json()["result"]
    return {"transactions": transactions}


@app.route("/time")
def get_current_time():
    return {"time": time.time()}
