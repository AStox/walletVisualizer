import requests
import os
import time
import datetime
import json
import re
import functools
from flask import Flask, request
from functools import reduce
from web3.auto.infura import w3
from liquidity_pool_returns import get_returns_windows, get_batched_returns
from price_fetcher import fetch_price_data
from utils import get_price, round_down_datetime


app = Flask(__name__)

my_account = os.environ.get("MY_ACC")
etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")

prices = json.load(open("prices.json", "r"))
old_contracts = json.load(open("contracts.json", "r"))
# old_contracts["owner"] = {value.lower(): key for key, value in old_contracts["address"].items()}

liquidity_positions = {}
liquidity_position_timestamps = {}
all_tokens = []
errors = []

@app.route("/")
def main():
    return "hi"

def percentChange(t1, t2):
    return ((t1-t2)/t2) * 100

def percent_change_calculations(transactions):
    for i, tx in enumerate(transactions[1:]):
        tx24h = transactions[i]
        tx1w = transactions[i-6]
        tx["_24hourChange"] = {}
        tx["_1weekChange"] = {}
        for _, symbol in enumerate(tx["balancesUSD"]):
            tx["_24hourChange"][symbol] = percentChange(tx["balancesUSD"][symbol], tx24h["balancesUSD"][symbol]) if tx24h["balancesUSD"].get(symbol) else None
            tx["_1weekChange"][symbol] = percentChange(tx["balancesUSD"][symbol], tx1w["balancesUSD"][symbol]) if tx1w["balancesUSD"].get(symbol) else None
        tx["_24hourChange"]["total"] = percentChange(tx["total_balance_USD"], tx24h["total_balance_USD"]) if tx24h["total_balance_USD"] else None
        tx["_1weekChange"]["total"] = percentChange(tx["total_balance_USD"], tx1w["total_balance_USD"]) if tx1w["total_balance_USD"] else None

def liquidity_returns_calculations(transactions, liquidity_returns):
    for tx in transactions:
        if liquidity_returns.get(tx["timeStamp"]):
            for _, symbol in enumerate(liquidity_returns[tx["timeStamp"]]):
                if liquidity_returns[tx["timeStamp"]][symbol]:
                    tx["balancesUSD"][symbol] = liquidity_returns[tx["timeStamp"]][symbol]["netValue"]

def sum(total, bal):
    return total + bal

def total_balance_calculations(transactions):
    for tx in transactions:
        tx["total_balance_USD"] = reduce(
            sum, tx["balancesUSD"].values(), 0
        )

def fill_out_dates(transactions):
    fill_dates = []
    for a, tx in enumerate(transactions[0:-2]):
        for i in [
            j * 60 * 60 * 24 + int(transactions[a]["timeStamp"])
            for j in range(
                0,
                int(
                    (
                        int(transactions[a + 1]["timeStamp"])
                        - int(transactions[a]["timeStamp"])
                    )
                    / (60 * 60 * 24)
                ),
            )
        ]:
            values = {}
            token_prices = {}
            for key, value in transactions[a]["values"].items():
                values[key] = 0
                token_prices[key] = get_price(i, key, prices)
            fill_dates.append(
                {
                    "timeStamp": i,
                    "values": values,
                    "prices": token_prices,
                    "isError": 0,
                }
            )

    for i in [
        j * 60 * 60 * 24 + int(transactions[-1]["timeStamp"])
        for j in range(
            0,
            int(
                datetime.datetime(*datetime.datetime.utcnow().timetuple()[:3]).timestamp()
                / (60 * 60 * 24)
                - int(transactions[-1]["timeStamp"]) / (60 * 60 * 24)
            )
        )
    ]:
        values = {}
        token_prices = {}
        for key, value in transactions[-1]["values"].items():
            values[key] = 0
            token_prices[key] = get_price(i, key, prices)
        fill_dates.append(
            {"timeStamp": i, "values": values, "prices": token_prices, "isError": 0}
        )

    now = int(datetime.datetime.now().timestamp())
    values = {}
    token_prices = {}
    for key, value in transactions[-1]["values"].items():
            values[key] = 0
            token_prices[key] = get_price(now, key, prices)
    fill_dates.append(
        {"timeStamp": now, "values": values, "prices": token_prices, "isError": 0}
    )
    for i in fill_dates:
        transactions.append(i)
    transactions.sort(key=sortTransactions)

    return transactions

def sortTransactions(e):
    return int(e["timeStamp"])

def balance_calc(balances, transaction, contracts):
    for i, key in enumerate(transaction["values"]):
        if not key in all_tokens:
            all_tokens.append(key)
        value = transaction["values"][key]
        balances[key] = (balances.get(key) or 0) + value
    transaction["balances"] = dict(balances)
    for token in transaction["balances"]:
        transaction["prices"][token] = get_price(transaction["timeStamp"], token, prices)
    tempBalArrays = [
        [key, balances[key], transaction["prices"], transaction["timeStamp"], contracts["WETH" if key == "ETH" else key]["address"]]
        for i, key in enumerate(balances)
    ]
    usd = reduce(balancesUSD, tempBalArrays, {})
    transaction["balancesUSD"] = dict(usd)
    # print(transaction["balances"])
    return balances

def is_uniswap_pool(symbol):
    return re.search(r"/", symbol) is not None

def balancesUSD(balances, balance_obj):
    [symbol, balance, prices_obj, timestamp, address] = balance_obj
    if is_uniswap_pool(symbol):
        # print(f"uniswap: {symbol}")
        if balance > 0.0000001:
            liquidity_position_timestamps[timestamp] = liquidity_position_timestamps.get(timestamp) or {}
            liquidity_position_timestamps[timestamp][symbol] = [liquidity_positions[symbol]["timestamp"], timestamp, address, balance]
    else:
        balance = (balance) * float(prices_obj.get(symbol) or 0.0)
        print(f"regular: {symbol}, price: {float(prices_obj.get(symbol) or 0.0)}, balance: {balance}")
        if balance >= 0.01:
            balances[symbol] = balance
    # print(balances)
    return balances

def group_by_date(transactions):
    grouped_tx = {}
    for tx in transactions:
        timestamp = str(round_down_datetime(tx["timeStamp"]))
        if grouped_tx.get(timestamp):
            grouped_tx[timestamp]["transactions"].append(tx)
        else:
            grouped_tx[timestamp] = {"transactions": [tx]}

    grouped_array = []
    for i, timestamp in enumerate(grouped_tx):
        grouped_tx[timestamp]["prices"] = prices.get(timestamp) or {}
        grouped_tx[timestamp]["timeStamp"] = timestamp
        grouped_tx[timestamp]["values"] = reduce(
            sum_values, grouped_tx[timestamp]["transactions"], {}
        )
        grouped_array.append(grouped_tx[timestamp])
    grouped_array[-1]["timeStamp"] = transactions[-1]["timeStamp"]    #the last date is now and should not be rounded down

    return grouped_array

def sum_values(sum, tx):
    values = sum
    for i, key in enumerate(tx["values"]):
        if int(tx["isError"]) == 0:
            values[key] = (sum.get(key) or 0) + tx["values"][key]
    return dict(values)

def liquidity_returns_calculations(transactions, liquidity_returns):
    for tx in transactions:
        if liquidity_returns.get(tx["timeStamp"]):
            for _, symbol in enumerate(liquidity_returns[tx["timeStamp"]]):
                if liquidity_returns[tx["timeStamp"]][symbol]:
                    tx["balancesUSD"][symbol] = liquidity_returns[tx["timeStamp"]][symbol]["netValue"]
                    # print(tx["balancesUSD"])


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
            contracts_data[symbol] = {"abi": abi, "address": value["address"], "name": name}

    for addr in addresses:
        response = requests.get(
            f'https://api.etherscan.io/api?module=contract&action=getabi&address={addr}&apikey={etherscan_api_key}'
        )
        if int(response.json()["status"]) == 1:
            abi = response.json()["result"]
            addr = w3.toChecksumAddress(addr)
            contract = w3.eth.contract(addr, abi=abi)
            if 'name' in dir(contract.functions):
                name = contract.functions.name().call()
                symbol = contract.functions.symbol().call()
                contracts_data[symbol] = { "abi": abi, "address": addr, "name": name}
    return contracts_data
        


@app.route("/wallet/<wallet>")
def get_transactions(wallet):
    wallet = wallet.lower()
    blockNumber = request.args.get("blockNumber")
    response = requests.get(
        f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet}&startblock={blockNumber}&endblock=99999999&sort=asc&apikey={etherscan_api_key}"
    )
    new_transactions = response.json()["result"]
    contracts = get_contracts_data(new_transactions, old_contracts)
    contracts["owner"] = {value["address"].lower(): key for key, value in contracts.items()}

    for transaction in new_transactions:
        transaction["values"] = {}
        transaction["prices"] = {}
        transaction["txCost"] = 0
        deposit = transaction["to"].lower() == wallet
        if transaction["from"].lower() == wallet.lower():
            transaction["txCost"] = float(
                w3.fromWei(
                    int(transaction["gasUsed"]) * int(transaction["gasPrice"]),
                    "ether",
                )
            )
            transaction["values"]["ETH"] = -transaction["txCost"]
        key = contracts["owner"].get(transaction["to"].lower())
        address = transaction["from"].lower()
        transaction["fromName"] = contracts["owner"].get(transaction["from"].lower())
        transaction["toName"] = key
        contract_data = contracts.get(key)
        contract_abi = contract_data.get("abi") if contract_data else None
        if int(transaction["isError"]) == 0:
            transaction["values"] = {
                "ETH": float(w3.fromWei(int(transaction["value"]), "ether"))
                * (1 if deposit else -1)
            }
            if contract_abi:
                contract_address = w3.toChecksumAddress(contracts[key]["address"])
                contract = w3.eth.contract(contract_address, abi=contract_abi)
                if len(transaction["input"]) > 4:
                    input = contract.decode_function_input(transaction["input"])
                    transaction["input"] = str(input)
                    func = input[0].fn_name
                    transaction["name"] = func
                    if func == "approve":
                        transaction["values"]["ETH"] -= transaction["txCost"]
                    if func == "swapExactTokensForETH":
                        address = input[1]["path"][0].lower()
                        token = contracts["owner"].get(address)
                        if token:
                            tokenContract = w3.eth.contract(
                                w3.toChecksumAddress(
                                    contracts[f"ETH/{token}"]["address"]
                                ),
                                abi=contracts[f"ETH/{token}"]["abi"],
                            )
                            # TODO: DONT USE BALANCEOF HERE IT WON"T SCALE
                            transaction["values"][f"ETH/{token}"] = float(
                                w3.fromWei(
                                    tokenContract.functions.balanceOf(
                                        w3.toChecksumAddress(wallet)
                                    ).call(),
                                    "ether",
                                )
                            )
                        pool = f"WETH/{token}"
                        tokenContract = w3.eth.contract(
                            w3.toChecksumAddress(contracts[pool]["address"]),
                            abi=contracts[pool]["abi"],
                        )
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        if len(logs) > 0:
                            transaction["values"]["ETH"] = (
                                float(
                                    w3.fromWei(
                                        tokenContract.events.Swap().processLog(
                                            logs[-2]
                                        )["args"]["amount1Out"],
                                        "ether",
                                    )
                                )
                                - transaction["txCost"]
                            )
                        if transaction["values"].get(token) == None:
                            transaction["values"][token] = 0
                        transaction["values"][token] = -float(
                            w3.fromWei(
                                tokenContract.events.Swap().processLog(logs[-2])[
                                    "args"
                                ]["amount0In"],
                                "ether",
                            )
                        )
                    if func == "swapETHForExactTokens":
                        address = input[1]["path"][-1].lower()
                        key = contracts["owner"].get(input[1]["path"][-1].lower())
                        txHash = transaction["hash"]
                        time.sleep(0.5)
                        internalTx = requests.get(
                            f"https://api.etherscan.io/api?module=account&action=txlistinternal&txhash={txHash}&apikey={etherscan_api_key}"
                        ).json()["result"]
                        for tx in internalTx:
                            if tx["to"].lower() == wallet:
                                transaction["values"]["ETH"] += (
                                    float(
                                        w3.fromWei(
                                            int(tx["value"]),
                                            "ether",
                                        )
                                    )
                                    - transaction["txCost"]
                                )

                        transaction["values"][key] = (
                            float(w3.fromWei(input[1]["amountOut"], "mwei"))
                            if key == "USDT"
                            else float(w3.fromWei(input[1]["amountOut"], "ether"))
                        )
                    if func == "swapExactETHForTokens":
                        address = input[1]["path"][-1].lower()
                        token = contracts['owner'].get(address)
                        pool = f"ETH/{token}" # We assume the user is using Uniswap to swap by doing this. BAD
                        if not token:
                            raise Exception(f"No token data for {address}")
                        txHash = transaction["hash"]
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        contract_abi = contracts[pool]["abi"]
                        contract_address = w3.toChecksumAddress(
                            contracts[pool]["address"]
                        )
                        contract = w3.eth.contract(contract_address, abi=contract_abi)
                        if len(logs) > 0:
                            transaction["values"][token] = float(
                                w3.fromWei(
                                    contract.events.Swap().processLog(logs[-1])["args"][
                                        "amount0Out"
                                    ],
                                    "ether",
                                )
                            )
                            transaction["values"]["ETH"] = (
                                -float(
                                    w3.fromWei(int(transaction["value"]), "ether"),
                                )
                                - transaction["txCost"]
                            )

                    if func == "addLiquidityETH":
                        address = input[1]["token"].lower()
                        token = contracts["owner"].get(address)
                        pool = f"WETH/{token}"
                        tokenContract = w3.eth.contract(
                            w3.toChecksumAddress(contracts[pool]["address"]),
                            abi=contracts[pool]["abi"],
                        )
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        if len(logs) > 0:
                            eth_pool = f"ETH/{token}"
                            if transaction["values"].get(eth_pool) == None:
                                transaction["values"][eth_pool] = 0
                            transaction["values"][eth_pool] = float(
                                w3.fromWei(
                                    tokenContract.events.Transfer().processLog(
                                        logs[-3]
                                    )["args"]["value"],
                                    "ether",
                                )
                            )
                            liquidity_positions[eth_pool] = {
                                "timestamp": int(transaction["timeStamp"]),
                                "token_bal": transaction["values"][eth_pool],
                            }
                            if token == "USDT":
                                transaction["values"]["ETH"] = (
                                    -float(
                                        w3.fromWei(
                                            tokenContract.events.Mint().processLog(
                                                logs[-1]
                                            )["args"]["amount0"],
                                            "ether",
                                        )
                                    )
                                    - transaction["txCost"]
                                )
                                if transaction["values"].get(token) == None:
                                    transaction["values"][token] = 0
                                transaction["values"][token] -= float(
                                    w3.fromWei(
                                        tokenContract.events.Mint().processLog(
                                            logs[-1]
                                        )["args"]["amount1"],
                                        "mwei",
                                    )
                                )
                            else:
                                transaction["values"]["ETH"] = (
                                    -float(
                                        w3.fromWei(
                                            tokenContract.events.Mint().processLog(
                                                logs[-1]
                                            )["args"]["amount1"],
                                            "ether",
                                        )
                                    )
                                    - transaction["txCost"]
                                )
                                if transaction["values"].get(token) == None:
                                    transaction["values"][token] = 0
                                transaction["values"][token] -= float(
                                    w3.fromWei(
                                        tokenContract.events.Mint().processLog(
                                            logs[-1]
                                        )["args"]["amount0"],
                                        "ether",
                                    )
                                )

                    if func == "stakeWithPermit":
                        transaction["values"]["ETH"] = -transaction["txCost"]
                    if func == "deposit":
                        transaction["values"]["ETH"] = -transaction["txCost"]
                    if func == "withdraw":
                        transaction["values"]["ETH"] = -transaction["txCost"]
                    if func == "removeLiquidityETHWithPermit":
                        address = input[1]["token"].lower()
                        token = contracts["owner"].get(address)
                        if token:
                            tokenContract = w3.eth.contract(
                                w3.toChecksumAddress(
                                    contracts[f"ETH/{token}"]["address"]
                                ),
                                abi=contracts[f"ETH/{token}"]["abi"],
                            )
                            # TODO: DONT USE BALANCEOF HERE IT WON"T SCALE
                            transaction["values"][f"ETH/{token}"] = float(
                                w3.fromWei(
                                    tokenContract.functions.balanceOf(
                                        w3.toChecksumAddress(wallet)
                                    ).call(),
                                    "ether",
                                )
                            )
                        pool = f"WETH/{token}"
                        tokenContract = w3.eth.contract(
                            w3.toChecksumAddress(contracts[pool]["address"]),
                            abi=contracts[pool]["abi"],
                        )
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        if len(logs) > 0:
                            transaction["values"]["ETH"] = (
                                float(
                                    w3.fromWei(
                                        tokenContract.events.Burn().processLog(
                                            logs[-3]
                                        )["args"]["amount1"],
                                        "ether",
                                    )
                                )
                                - transaction["txCost"]
                            )
                        if transaction["values"].get(token) == None:
                            transaction["values"][token] = 0
                        transaction["values"][token] = float(
                            w3.fromWei(
                                tokenContract.events.Burn().processLog(logs[-3])[
                                    "args"
                                ]["amount0"],
                                "ether",
                            )
                        )
                    if func == "exit":
                        transaction["values"]["ETH"] = -transaction["txCost"]

    new_transactions =  new_transactions
    last_block_number = new_transactions[-1]["blockNumber"]
    new_transactions = fill_out_dates(new_transactions)

    new_transactions = group_by_date(new_transactions)
    global prices
    prices = {**prices, **fetch_price_data(new_transactions, contracts)}

    reduce(functools.partial(balance_calc, contracts=contracts), new_transactions, {})
    liquidity_returns = get_batched_returns(liquidity_position_timestamps)
    liquidity_returns_calculations(new_transactions, liquidity_returns)
    total_balance_calculations(new_transactions)
    percent_change_calculations(new_transactions)
    addressData = {"transactions": new_transactions, "all_tokens": all_tokens, "last_block_number": last_block_number}
    return addressData

