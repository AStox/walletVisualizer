import requests
import os
import time
import datetime
import json
import functools
from flask import Flask, request
from functools import reduce
from web3.auto.infura import w3

from liquidity_pool_returns import get_returns_windows, get_batched_returns
from price_fetcher import fetch_price_data
from contracts import get_contracts_data
from prices import PriceInfo, percent_change_calculations, liquidity_returns_calculations, total_balance_calculations, balance_calc
from utils import get_price, round_down_datetime


app = Flask(__name__)

my_account = os.environ.get("MY_ACC")
etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")

old_contracts = json.load(open("contracts.json", "r"))
# old_contracts["owner"] = {value.lower(): key for key, value in old_contracts["address"].items()}

errors = []

@app.route("/")
def main():
    return "hi"

def days_between_transactions(timestamp1, timestamp2):
    return range(0, int((int(timestamp2) - int(timestamp1))/ (60 * 60 * 24)))

def timestamps_between_transactions(timestamp1, timestamp2):
    return [j * 60 * 60 * 24 + int(timestamp1) for j in days_between_transactions(timestamp1, timestamp2)]

def fill_out_dates(transactions):
    fill_dates = []
    prices = PriceInfo.getInstance().prices
    # Filling in dates up to the last transaction
    for tx_index, tx in enumerate(transactions[0:-1]):
        for i in timestamps_between_transactions(transactions[tx_index]["timeStamp"], transactions[tx_index + 1]["timeStamp"]):
            values = {}
            token_prices = {}
            for key, value in transactions[tx_index]["values"].items():
                values[key] = 0
                token_prices[key] = get_price(i, key, PriceInfo.getInstance().prices)
            fill_dates.append(
                {
                    "timeStamp": i,
                    "values": values,
                    "prices": token_prices,
                    "isError": 0,
                }
            )

    # Filling in dates from the last transaction until now
    now_timestamp = datetime.datetime(*datetime.datetime.utcnow().timetuple()[:3]).timestamp()
    for i in timestamps_between_transactions(transactions[-1]["timeStamp"], now_timestamp):
        values = {}
        token_prices = {}
        for key, value in transactions[-1]["values"].items():
            values[key] = 0
            token_prices[key] = get_price(i, key, prices)
        fill_dates.append(
            {"timeStamp": i, "values": values, "prices": token_prices, "isError": 0}
        )
    # FIXME: This is using local time, but tx timestamps are in UTC. This should changed to UTC
    # and timezone conversion should be done later or on the frontend
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
        grouped_tx[timestamp]["prices"] = PriceInfo.getInstance().prices.get(timestamp) or {}
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


@app.route("/wallet/<wallet>")
def get_transactions(wallet):
    print("Request received...")
    price_info = PriceInfo()
    price_info.prices = json.load(open("prices.json", "r"))
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
                "ETH": int(transaction["value"])/pow(10, contracts["WETH"]["decimals"])
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
                                tokenContract.functions.balanceOf(
                                    w3.toChecksumAddress(wallet)
                                ).call()/pow(10,contracts[f"ETH/{token}"]["decimals"])
                            )
                        pool = f"WETH/{token}"
                        tokenContract = w3.eth.contract(
                            w3.toChecksumAddress(contracts[pool]["address"]),
                            abi=contracts[pool]["abi"],
                        )
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        if len(logs) > 0:
                            transaction["values"]["ETH"] = tokenContract.events.Swap().processLog(logs[-2])["args"]["amount1Out"]/pow(10,contracts["WETH"]["decimals"])- transaction["txCost"]
                        if transaction["values"].get(token) == None:
                            transaction["values"][token] = 0
                        transaction["values"][token] = -tokenContract.events.Swap().processLog(logs[-2])["args"]["amount0In"]/pow(10,contracts[token]["decimals"])
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
                                            int(tx["value"])/pow(10,contracts["WETH"]["decimals"])
                                    - transaction["txCost"]
                                )

                        transaction["values"][key] = (
                                input[1]["amountOut"]/pow(10,contracts[key]["decimals"])
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
                            transaction["values"][token] = contract.events.Swap().processLog(logs[-1])["args"]["amount0Out"]/pow(10,contracts[token]["decimals"])
                            transaction["values"]["ETH"] = (-int(transaction["value"])/pow(10,contracts[key]["decimals"])- transaction["txCost"])

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
                            transaction["values"][eth_pool] = tokenContract.events.Transfer().processLog(logs[-3])["args"]["value"]/pow(10,contracts[eth_pool]["decimals"])
                            price_info.liquidity_positions[eth_pool] = {
                                "timestamp": int(transaction["timeStamp"]),
                                "token_bal": transaction["values"][eth_pool],
                            }
                            transaction["values"]["ETH"] = -tokenContract.events.Mint().processLog(logs[-1])["args"]["amount1"]/pow(10,contracts["WETH"]["decimals"])- transaction["txCost"]
                            if transaction["values"].get(token) == None:
                                transaction["values"][token] = 0
                            transaction["values"][token] -= tokenContract.events.Mint().processLog(logs[-1])["args"]["amount0"]/pow(10,contracts[token]["decimals"])

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
                            transaction["values"][f"ETH/{token}"] = tokenContract.functions.balanceOf(w3.toChecksumAddress(wallet)).call()/pow(10,contracts[f"ETH/{token}"]["decimals"])
                        pool = f"WETH/{token}"
                        tokenContract = w3.eth.contract(
                            w3.toChecksumAddress(contracts[pool]["address"]),
                            abi=contracts[pool]["abi"],
                        )
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        if len(logs) > 0:
                            transaction["values"]["ETH"] = (tokenContract.events.Burn().processLog(logs[-3])["args"]["amount1"])/pow(10,contracts["WETH"]["decimals"])- transaction["txCost"]
                        if transaction["values"].get(token) == None:
                            transaction["values"][token] = 0
                        transaction["values"][token] = tokenContract.events.Burn().processLog(logs[-3])["args"]["amount0"]/pow(10,contracts[key]["decimals"])
                    if func == "exit":
                        transaction["values"]["ETH"] = -transaction["txCost"]

    new_transactions =  new_transactions
    last_block_number = new_transactions[-1]["blockNumber"]
    new_transactions = fill_out_dates(new_transactions)

    new_transactions = group_by_date(new_transactions)
    price_info.prices = {**price_info.prices, **fetch_price_data(new_transactions, contracts)}

    reduce(functools.partial(balance_calc, contracts=contracts), new_transactions, {})
    liquidity_returns = get_batched_returns(price_info.liquidity_position_timestamps)
    liquidity_returns_calculations(new_transactions, liquidity_returns)
    total_balance_calculations(new_transactions)
    percent_change_calculations(new_transactions)
    addressData = {"transactions": new_transactions, "all_tokens": price_info.all_tokens, "last_block_number": last_block_number}
    return addressData

