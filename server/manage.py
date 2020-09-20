from web3.auto.infura import w3
import requests

import os

my_account = os.environ.get("MY_ACC")
etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")

balance = w3.eth.getBalance(os.environ.get("MY_ACC"))
block = w3.eth.getBlock("latest").transactions

response = requests.get(
    f"https://api.etherscan.io/api?module=account&action=txlist&address=0xddbd2b932c763ba5b1b7ae3b362eac3e8d40121a&startblock=0&endblock=99999999&sort=asc&apikey={etherscan_api_key}"
)
transactions = response.json()["result"]

print(transactions)

print(w3.eth.blockNumber)
print(balance * 0.000000000000000001)


def get_transaction_details(transaction):
    return w3.eth.getTransaction(transaction)


def get_address_transactions(address):
    i = 0
    while i < w3.eth.blockNumber:
        block = w3.eth.getBlock(i)
        print("Block:", i)
        for transaction in block.transactions:
            detail = get_transaction_details(transaction)
            print(detail)
        i += 1


# get_address_transactions(my_account)