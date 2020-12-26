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

    def get_contract(self, address=None, symbol=None):
        if symbol:
            if self.contracts.get(symbol):
                return self.contracts[symbol]
        if address:
            address = w3.toChecksumAddress(address)
            for key, value in self.contracts.items():
                if address in value.address:
                    if symbol:
                        self.contracts[symbol] = value
                        self.contracts.pop(key)
                    return value
            return self.add_contract(address, key=symbol)
    
    def populate_contract_data(self, transactions, special_contracts):
        for key, value in special_contracts.items():
            abi = fetch_abi(value["address"])
            if abi:
                name = key
                symbol = key
                contract = w3.eth.contract(w3.toChecksumAddress(value["address"]), abi=abi)
                decimals = None
                if 'decimals' in dir(contract.functions):
                    decimals = contract.functions.decimals().call()
                self.contracts[symbol] = Contract(abi=abi, symbol=symbol, address=value["address"], name=name, decimals=decimals)
        return self.contracts

    def add_contract(self, address, key=None):
        address = w3.toChecksumAddress(address)
        abi = fetch_abi(address)
        if abi:
            contract = w3.eth.contract(address, abi=abi)
            if 'name' in dir(contract.functions):
                name = contract.functions.name().call()
                symbol = contract.functions.symbol().call()
                decimals = contract.functions.decimals().call()
                self.contracts[key or symbol] = Contract(abi=abi, symbol=symbol, address=address, name=name, decimals=decimals)
                print(f"Adding contract {key or symbol}")
                return self.contracts[key or symbol]
            else:
                self.contracts[key or address] = Contract(abi=abi, address=address)
                print(f"Adding contract {key or address}")
                return self.contracts[key or address]
        return None


class Contract:
    def __init__(self, abi, address, name=None, symbol=None, decimals=18):
        self.abi = abi
        self.address = address
        self.name = name
        self.symbol = symbol
        self.decimals = decimals
        self.w3_contract = w3.eth.contract(w3.toChecksumAddress(address), abi=abi)


def fetch_uniswap_pool_contract(token1, token2, contracts, key=None):
    token1 = w3.toChecksumAddress(token1)
    token2 = w3.toChecksumAddress(token2)
    factory = contracts["UniswapFactory"].w3_contract
    pool = factory.functions.getPair(token1, token2).call()
    contract = Contracts.getInstance().get_contract(pool, symbol=key)
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

special_contracts = {
    "WETH": { 
        "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2" 
    }, 
    "UniswapFactory": { 
        "address": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f" 
    },
    "SHAKEPAY": {
        "address": [
        "0x81b019a5c85adf9045140f689154faecdf20b0bf",
        "0xa2948dcffa94ef110f880675f05b112bdf9750c2",
        "0x90e577775a9f2130979a041d99a6e7af1835f79d",
        "0xbd20672851a3b7588ad1c5b83027dcdd566b0d10",
        "0x92104f9c660b85e9e35c2ec69a81809f3aa95b76",
        "0xaecec7358bb34ee28942ca671aa7a182705f19b6",
        "0xf72bf7668067ca892f6066a702cf2d19e78a7909",
        "0x9bdfaa68548dfde712898bcd0f1ebd2225244224"
        ]
    },
    "BTCtoETH": { "address": "0xe7324d9ac91abcd37aed8e9c8846791ebfd16513" },
    "METAMASK": { "address": "0x225ef95fa90f4F7938A5b34234d14768cB4263dd" },
    "GEMINI": { "address": "0x2c942d438f8e4b7b49252e896ee4745ca6d96aea" },
    "MEW": { "address": "0x0d74c19b87cee6d9d4f843e2ddb5f8bc2dd42c08" }
}