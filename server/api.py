import time
import requests
import os
from flask import Flask

# import ./contracts.json as contracts
import json

contracts = json.load(open("contracts.json", "r"))

app = Flask(__name__)

my_account = os.environ.get("MY_ACC")
etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")


@app.route("/")
def main():
    return "hi"


def find_tokens(transaction):
    contract = w3.eth.contract(contract_address, abi=ether_abi)


@app.route("/wallet/<wallet>")
def get_transactions(wallet):
    response = requests.get(
        f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet}&startblock=0&endblock=99999999&sort=asc&apikey={etherscan_api_key}"
    )
    transactions = response.json()["result"]
    for transaction in transactions:
        transaction["values"] = {
            "ETH": float(transaction["value"]) * 0.000000000000000001
        }
        for key, address in contracts["address"].items():
            if transaction["to"].lower() == address.lower():
                print(key)
                transaction["values"][key] = 2
                print(transaction["values"])

    return {"transactions": transactions}
