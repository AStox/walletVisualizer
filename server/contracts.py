import requests
import os
import json
from web3.auto.infura import w3

etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")

class Contracts:
    __instance = None
    def __init__(self):
        if Contracts.__instance != None:
            raise Exception("Contracts already exists")
        else:
            Contracts.__instance = self

    contracts = {}

    @staticmethod 
    def getInstance():
        if Contracts.__instance == None:
            Contracts()
        return Contracts.__instance

    def get_contract(self, symbol=None, address=None):
        if symbol:
            return self.contracts[symbol]
        if address:
            for key, value in self.contracts.items():
                if address in value.address:
                    return value
            return self.add_contract(address)
    
    def populate_contract_data(self, transactions, old_contracts):
        contracts_data = {}
        addresses = collect_addresses(transactions)
        
        # for key, value in old_contracts.items():
        #     abi = fetch_address(value["address"], old_contracts)
        #     if abi:
        #         name = key
        #         symbol = key
        #         contracts_data[symbol] = Contract("abi": abi, "address": value["address"], "name": name, "decimals": value.get("decimals") or 18})
        special_contracts = {"WETH": { "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2" }, "UniswapFactory": { "address": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f" }}
        for key, value in special_contracts.items():
            abi = fetch_abi(value["address"])
            if abi:
                name = key
                symbol = key
                self.contracts[symbol] = Contract(abi=abi, symbol=symbol, address=value["address"], name=name, decimals=value.get("decimals") or 18)
        for addr in addresses:
            self.add_contract(addr)
        print([key for key, value in self.contracts.items()])
        return self.contracts

    def add_contract(self, address):
        address = w3.toChecksumAddress(address)
        abi = fetch_abi(address)
        if abi:
            contract = w3.eth.contract(address, abi=abi)
            if 'name' in dir(contract.functions):
                name = contract.functions.name().call()
                symbol = contract.functions.symbol().call()
                decimals = contract.functions.decimals().call()
                self.contracts[symbol] = Contract(abi=abi, symbol=symbol, address=address, name=name, decimals=decimals)
                return self.contracts[symbol]
            else:
                self.contracts[address] = Contract(abi=abi, address=address)
                return self.contracts[address]
        return None

class Contract:
    def __init__(self, abi, address, name=None, symbol=None, decimals=18):
        self.abi = abi
        self.address = address
        self.name = name
        self.symbol = symbol
        self.decimals = decimals
        self.w3_contract = w3.eth.contract(w3.toChecksumAddress(address), abi=abi)

def fetch_uniswap_pool_contract(token1, token2, contracts, name=None):
    token1 = w3.toChecksumAddress(token1)
    token2 = w3.toChecksumAddress(token2)
    factory = w3.eth.contract(
            w3.toChecksumAddress(contracts["UniswapFactory"].address),
            abi=contracts["UniswapFactory"].abi,
        )
    pool = factory.functions.getPair(token1, token2).call()
    pool_abi = fetch_abi(pool)
    contract = w3.eth.contract(w3.toChecksumAddress(pool), abi=pool_abi)
    name = contract.functions.name().call()
    symbol = contract.functions.symbol().call()
    decimals = contract.functions.decimals().call()
    contracts[name or pool] = Contract(abi=pool_abi, address=pool, name=name, decimals=decimals)
    return contract

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

def fetch_abi(address, old_contracts=None, debug=False):
    response = requests.get(
        f'https://api.etherscan.io/api?module=contract&action=getabi&address={address}&apikey={etherscan_api_key}'
    )
    if int(response.json()["status"]) == 1:
        return response.json()["result"]
    else:
        if debug:
            if (old_contracts):
                for key, value in old_contracts.items():
                    if address.lower() in value["address"]:
                        print(key, " : ", address, response.json())
                        return None
            print(address, response.json())
        return None
