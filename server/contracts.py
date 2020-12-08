import requests
import os
import json
from web3.auto.infura import w3

etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")

def collect_addresses(transactions):
    addresses = []
    for tx in transactions:
        addr = tx["to"].lower()
        if not addr in addresses:
            addresses.append(addr)
        addr = tx["from"].lower()
        if not addr in addresses:
            addresses.append(addr)
    return addresses


def get_contracts_data(transactions, old_contracts):
    contracts_data = {}
    addresses = collect_addresses(transactions)
    
    for key, value in old_contracts.items():
        response = requests.get(
            f'https://api.etherscan.io/api?module=contract&action=getabi&address={value["address"]}&apikey={etherscan_api_key}'
        )
        if int(response.json()["status"]) == 1:
            abi = response.json()["result"]
            name = key
            symbol = key
            contracts_data[symbol] = {"abi": abi, "address": value["address"], "name": name, "decimals": value.get("decimals") or 18}

    for addr in addresses:
        response = requests.get(
            f'https://api.etherscan.io/api?module=contract&action=getabi&address={addr}&apikey={etherscan_api_key}'
        )
        if int(response.json()["status"]) == 1:
            abi = response.json()["result"]
            addr = w3.toChecksumAddress(addr)
            contract = w3.eth.contract(addr, abi=abi)
            if 'name' in dir(contract.functions):
                # print(dir(contract.functions))
                name = contract.functions.name().call()
                symbol = contract.functions.symbol().call()
                decimals = contract.functions.decimals().call()
                contracts_data[symbol] = { "abi": abi, "address": addr, "name": name, "decimals": decimals}
    return contracts_data