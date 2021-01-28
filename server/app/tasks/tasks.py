import requests
import time
import json
import functools
import os
from app import celery
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import Flask, url_for
from web3 import Web3, exceptions
from app.liquidity_pool_returns import get_batched_returns
from app.price_fetcher import PriceFetcher
from app.contracts import Contracts, fetch_abi
from app.prices import PriceInfo, percent_change_calculations, liquidity_returns_calculations, total_balance_calculations, balance_calc
from app.transactions import fill_out_dates, group_by_date
from functools import reduce
from numpy import copy
# from web3.auto.infura import w3

w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{os.environ.get("WEB3_INFURA_PROJECT_ID")}'))

my_account = os.environ.get("MY_ACC")
etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")

special_contracts = json.load(open("app/contracts.json", "r"))

def increment():
    global current
    current += 1
    return current

@celery.task(bind=True)
def get_transactions(self, wallet, blockNumber):
    self.update_state(state='PROGRESS', meta={'current': 0, 'total': 0,'status': "Starting..."})
    price_info = PriceInfo.get_instance()
    contracts_info = Contracts.get_instance()
    price_info.prices = json.load(open("prices.json", "r"))
    wallet = w3.toChecksumAddress(wallet)
    response = requests.get(
        f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet}&startblock={blockNumber}&endblock=99999999&sort=asc&apikey={etherscan_api_key}"
    )
    new_transactions = response.json()["result"]
    contracts_info.populate_contract_data(new_transactions, special_contracts)
    contracts = contracts_info.contracts
    
    temp_transactions = new_transactions.copy()
    # This is wasteful! Just need the final number of transactions
    temp_transactions = fill_out_dates(temp_transactions)
    batch_count = PriceFetcher(self, transactions=temp_transactions).batch_count
    total = len(new_transactions) + batch_count
    global current
    current = 0

    for index, transaction in enumerate(new_transactions):
        try:
            self.update_state(state='PROGRESS', meta={'current': increment(), 'total': total,'status': "Processing transactions..."})
            transaction["values"] = {}
            transaction["prices"] = {}
            transaction["txCost"] = 0
            transaction["to"] = w3.toChecksumAddress(transaction["to"])
            transaction["from"] = w3.toChecksumAddress(transaction["from"])
            deposit = transaction["to"] == wallet
            if transaction["from"] == wallet:
                transaction["txCost"] = float(
                    w3.fromWei(
                        int(transaction["gasUsed"]) * int(transaction["gasPrice"]),
                        "ether",
                    )
                )
                transaction["values"]["ETH"] = -transaction["txCost"]
            from_contract = contracts_info.get_contract(address=transaction["from"])
            to_contract = contracts_info.get_contract(address=transaction["to"])
            transaction["fromName"] = from_contract.symbol() if from_contract else ""
            transaction["toName"] = to_contract.symbol() if to_contract else ""
            contract_abi = to_contract.abi if to_contract else None
            if int(transaction["isError"]) == 0:
                transaction["values"] = {
                    "ETH": int(transaction["value"])/pow(10, contracts["ETH"].decimals)
                    * (1 if deposit else -1)
                }
                if contract_abi:
                    contract_address = w3.toChecksumAddress(to_contract.address)
                    contract = w3.eth.contract(contract_address, abi=contract_abi)
                    if len(transaction["input"]) > 4:
                        input = contract.decode_function_input(transaction["input"])
                        transaction["input"] = str(input)
                        func = input[0].fn_name
                        transaction["name"] = func
                        if func == "approve":
                            transaction["values"]["ETH"] -= transaction["txCost"]
                        if func == "swapExactTokensForETH":
                            token1 = contracts["ETH"].address
                            token2 = input[1]["path"][0]
                            tokenContract = contracts_info.get_contract(token2)
                            poolContract = contracts_info.fetch_uniswap_pool_contract(token1, token2)
                            poolDecimals = poolContract.decimals
                            pool_symbols = [contracts_info.get_contract(poolContract.w3_contract.functions.token0().call()).symbol(),contracts_info.get_contract(poolContract.w3_contract.functions.token1().call()).symbol()]
                            logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                            if len(logs) > 0:
                                transaction["values"]["ETH"] = poolContract.w3_contract.events.Swap().processLog(logs[-2])["args"][f"amount{pool_symbols.index('ETH')}Out"]/pow(10,contracts["ETH"].decimals)- transaction["txCost"]
                                transaction["values"][tokenContract.symbol()] = -poolContract.w3_contract.events.Swap().processLog(logs[-2])["args"][f"amount{pool_symbols.index(tokenContract.symbol())}In"]/pow(10, tokenContract.decimals)
                        if func == "swapETHForExactTokens":
                            address = input[1]["path"][-1]
                            token_contract = contracts_info.get_contract(address=address)
                            txHash = transaction["hash"]
                            time.sleep(0.1)
                            internalTx = requests.get(
                                f"https://api.etherscan.io/api?module=account&action=txlistinternal&txhash={txHash}&apikey={etherscan_api_key}"
                            ).json()["result"]
                            for tx in internalTx:
                                if tx["to"].lower() == wallet:
                                    transaction["values"]["ETH"] += (
                                                int(tx["value"])/pow(10,contracts["ETH"].decimals)
                                        - transaction["txCost"]
                                    )

                            transaction["values"][token_contract.symbol()] = (
                                    input[1]["amountOut"]/pow(10,token_contract.decimals)
                            )
                        if func == "swapExactETHForTokens":
                            token1 = contracts["ETH"].address
                            token2 = input[1]["path"][-1].lower()
                            tokenContract = contracts_info.get_contract(token2)
                            poolContract = contracts_info.fetch_uniswap_pool_contract(token1, token2,)
                            poolDecimals = poolContract.decimals
                            txHash = transaction["hash"]
                            logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                            if len(logs) > 0:
                                transaction["values"][tokenContract.symbol()] = poolContract.w3_contract.events.Swap().processLog(logs[-1])["args"]["amount0Out"]/pow(10, tokenContract.decimals)
                                transaction["values"]["ETH"] = (-int(transaction["value"])/pow(10, poolDecimals)- transaction["txCost"])

                        if func == "addLiquidityETH":
                            token_a = contracts["ETH"].address
                            token_b = input[1]["token"]
                            tokenContract = contracts_info.get_contract(token_b)
                            poolContract = contracts_info.fetch_uniswap_pool_contract(token_a, token_b)
                            poolDecimals = poolContract.decimals
                            pool_symbols = [contracts_info.get_contract(poolContract.w3_contract.functions.token0().call()).symbol(),contracts_info.get_contract(poolContract.w3_contract.functions.token1().call()).symbol()]
                            logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                            if len(logs) > 0:
                                transaction["values"][poolContract.symbol()] = poolContract.w3_contract.events.Transfer().processLog(logs[-3])["args"]["value"]/pow(10,poolDecimals)
                                price_info.liquidity_positions[poolContract.symbol()] = {
                                    "timestamp": int(transaction["timeStamp"]),
                                    "token_bal": transaction["values"][poolContract.symbol()],
                                }
                                transaction["values"]["ETH"] = -poolContract.w3_contract.events.Mint().processLog(logs[-1])["args"][f"amount{pool_symbols.index('ETH')}"]/pow(10,contracts["ETH"].decimals)- transaction["txCost"]
                                if transaction["values"].get(tokenContract.symbol()) == None:
                                    transaction["values"][tokenContract.symbol()] = 0
                                transaction["values"][tokenContract.symbol()] -= poolContract.w3_contract.events.Mint().processLog(logs[-1])["args"][f"amount{pool_symbols.index(tokenContract.symbol())}"]/pow(10,tokenContract.decimals)

                        if func == "removeLiquidityETHWithPermit":
                            token2 = input[1]["token"]
                            token1 = contracts["ETH"].address
                            tokenContract = contracts_info.get_contract(token2)
                            poolContract = contracts_info.fetch_uniswap_pool_contract(token1, token2)
                            poolDecimals = poolContract.decimals
                            pool_symbols = [contracts_info.get_contract(poolContract.w3_contract.functions.token0().call()).symbol(),contracts_info.get_contract(poolContract.w3_contract.functions.token1().call()).symbol()]
                            logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                            if len(logs) > 0:
                                transaction["values"][poolContract.symbol()] = -(poolContract.w3_contract.events.Transfer().processLog(logs[1])["args"]["value"])/pow(10, poolDecimals)
                                transaction["values"]["ETH"] = (poolContract.w3_contract.events.Burn().processLog(logs[-3])["args"][f"amount{pool_symbols.index('ETH')}"])/pow(10,contracts["ETH"].decimals)- transaction["txCost"]
                            # if transaction["values"].get(tokenContract.symbol()) == None:
                            #     transaction["values"][tokenContract.symbol()] = 0
                            transaction["values"][tokenContract.symbol()] = poolContract.w3_contract.events.Burn().processLog(logs[-3])["args"][f"amount{pool_symbols.index(tokenContract.symbol())}"]/pow(10, tokenContract.decimals)
                        if func == "stakeWithPermit":
                            transaction["values"]["ETH"] = -transaction["txCost"]
                        if func == "deposit":
                            transaction["values"]["ETH"] = -transaction["txCost"]
                            print(input[1])
                        if func == "withdraw":
                            logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                            for log in logs:
                                transaction_contract = contracts_info.get_contract(log["address"])
                                try:
                                    transfer = transaction_contract.w3_contract.events.Transfer().processLog(log)
                                    if w3.toChecksumAddress(transfer["args"]["to"]) == wallet:
                                        token_contract = contracts_info.get_contract(transfer["address"])
                                        transaction["values"][token_contract.symbol()] = transfer["args"]["value"]/pow(10, token_contract.decimals)
                                except exceptions.ABIEventFunctionNotFound:
                                    pass
                            transaction["values"]["ETH"] = -transaction["txCost"]
                            
                        if func == "exit":
                            transaction["values"]["ETH"] = -transaction["txCost"]
                        if func == "transfer":
                            transaction["values"][to_contract.symbol()] = -(input[1]['wad'])/pow(10, to_contract.decimals)
                            transaction["values"]["ETH"] = -transaction["txCost"]
                        print(func)
        except:
            pass

    new_transactions =  new_transactions
    last_block_number = new_transactions[-1]["blockNumber"]
    new_transactions = fill_out_dates(new_transactions)
    new_transactions = group_by_date(new_transactions)

    def update():
        self.update_state(state='PROGRESS', meta={'current': increment(), 'total': total,'status': "Fetching historical prices..."})

    price_fetcher = PriceFetcher(on_update=update, transactions=new_transactions)
    price_info.prices = {**price_info.prices, **price_fetcher.fetch_price_data()}

    self.update_state(state='PROGRESS', meta={'current': increment(), 'total': total,'status': "Compiling token balances..."})
    reduce(balance_calc, new_transactions, {})

    self.update_state(state='PROGRESS', meta={'current': increment(), 'total': total,'status': "Calculating staked liquidity returns..."})
    liquidity_returns = get_batched_returns(price_info.liquidity_position_timestamps)
    liquidity_returns_calculations(new_transactions, liquidity_returns)

    self.update_state(state='PROGRESS', meta={'current': increment(), 'total': total,'status': "Calculating percent changes..."})
    total_balance_calculations(new_transactions)
    percent_change_calculations(new_transactions)

    addressData = {"transactions": new_transactions, "all_tokens": price_info.all_tokens, "last_block_number": last_block_number}
    return {'current': increment(), 'total': total, 'status': 'Finished!',
            'result': addressData}

app.tasks.register(get_transactions())
app.tasks.register(test_task())