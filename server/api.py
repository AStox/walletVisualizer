import requests
import os
import time
import datetime
import json
from flask import Flask
from functools import reduce
from web3.auto.infura import w3
from uniswap import Uniswap
from eth_abi import decode_single, decode_abi


app = Flask(__name__)

my_account = os.environ.get("MY_ACC")
etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")

eth = "0x0000000000000000000000000000000000000000"
bat = "0x0D8775F648430679A709E98d2b0Cb6250d2887EF"
dai = "0x89d24A6b4CcB1B6fAA2625fE562bDD9a23260359"

prices = json.load(open("prices.json", "r"))
contracts = json.load(open("contracts.json", "r"))
contracts["owner"] = {value.lower(): key for key, value in contracts["address"].items()}


@app.route("/")
def main():
    return "hi"


def find_tokens(transaction, contract_abi, contract_address):
    return w3.eth.contract(contract_address, abi=ether_abi)


def get_token_balance(my_address, token_name, block="latest"):
    my_address = w3.toChecksumAddress(my_address)
    contract_abi = contracts["abi"][token_name]
    contract_address = w3.toChecksumAddress(contracts["address"][token_name])
    contract = w3.eth.contract(contract_address, abi=contract_abi)
    balance = contract.functions.balanceOf(my_address).call()
    return


@app.route("/wallet/<wallet>")
def get_transactions(wallet):
    wallet = wallet.lower()
    uniswap_wrapper = Uniswap(web3=w3, private_key=None, address=wallet)
    response = requests.get(
        f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet}&startblock=0&endblock=99999999&sort=asc&apikey={etherscan_api_key}"
    )
    transactions = response.json()["result"]
    for transaction in transactions:
        transaction["values"] = {}
        transaction["prices"] = {}
        deposit = transaction["to"].lower() == wallet
        transaction["txCost"] = 0
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
        contract_abi = contracts["abi"].get(key)
        if int(transaction["isError"]) == 0:
            transaction["values"] = {
                "ETH": float(w3.fromWei(int(transaction["value"]), "ether"))
                * (1 if deposit else -1)
            }
            # block = transaction["blockNumber"]
            if contract_abi:
                contract_address = w3.toChecksumAddress(contracts["address"][key])
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
                                    contracts["address"][f"ETH/{token}"]
                                ),
                                abi=contracts["abi"][f"ETH/{token}"],
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
                            w3.toChecksumAddress(contracts["address"][pool]),
                            abi=contracts["abi"][pool],
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
                        token = contracts["owner"].get(address)
                        txHash = transaction["hash"]
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        contract_abi = contracts["abi"][f"ETH/{token}"]
                        contract_address = w3.toChecksumAddress(
                            contracts["address"][f"ETH/{token}"]
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
                        if token:
                            tokenContract = w3.eth.contract(
                                w3.toChecksumAddress(
                                    contracts["address"][f"ETH/{token}"]
                                ),
                                abi=contracts["abi"][f"ETH/{token}"],
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
                            w3.toChecksumAddress(contracts["address"][pool]),
                            abi=contracts["abi"][pool],
                        )
                        logs = w3.eth.getTransactionReceipt(transaction["hash"])["logs"]
                        if len(logs) > 0:
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
                                    contracts["address"][f"ETH/{token}"]
                                ),
                                abi=contracts["abi"][f"ETH/{token}"],
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
                            w3.toChecksumAddress(contracts["address"][pool]),
                            abi=contracts["abi"][pool],
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

    transactions = fill_out_dates(transactions)

    reduce(balance_calc, transactions, {})

    return {"transactions": transactions}


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
                token_prices[key] = prices[str(round_down_datetime(i))].get(key)
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
                (
                    (
                        datetime.datetime(
                            *datetime.datetime.utcnow().timetuple()[:3]
                        ).timestamp()
                        / (60 * 60 * 24)
                        - int(transactions[-1]["timeStamp"]) / (60 * 60 * 24)
                    )
                )
            ),
        )
    ]:
        values = {}
        token_prices = {}
        for key, value in transactions[-1]["values"].items():
            values[key] = 0
            token_prices[key] = (
                prices.get(str(round_down_datetime(i))).get(key)
                if prices.get(str(round_down_datetime(i)))
                else 0
            )
        fill_dates.append(
            {"timeStamp": i, "values": values, "prices": token_prices, "isError": 0}
        )

    for i in fill_dates:
        transactions.append(i)
    transactions.sort(key=sortTransactions)

    return transactions


def sortTransactions(e):
    return int(e["timeStamp"])


def round_down_datetime(timestamp):
    return int(
        datetime.datetime(
            *datetime.datetime.fromtimestamp(int(timestamp)).timetuple()[:3]
        ).timestamp()
    )


def balance_calc(balances, transaction):
    for i, key in enumerate(transaction["values"]):
        value = transaction["values"][key]
        balances[key] = (balances.get(key) or 0) + value
    transaction["balances"] = dict(balances)
    for token in transaction["balances"]:
        transaction["prices"][token] = (
            prices[str(round_down_datetime(transaction["timeStamp"]))].get(token) or 0
        )
    tempBalArrays = [
        [key, balances[key], transaction["prices"]] for i, key in enumerate(balances)
    ]
    usd = reduce(balancesUSD, tempBalArrays, {})
    transaction["balancesUSD"] = dict(usd)
    return balances


def balancesUSD(balances, pair):
    balances[pair[0]] = (pair[1]) * float(pair[2].get(pair[0]) or 0.0)
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

    reduce(balance_calc, grouped_array, {})

    return grouped_array


def sum_values(sum, tx):
    values = sum
    for i, key in enumerate(tx["values"]):
        if int(tx["isError"]) == 0:
            values[key] = (sum.get(key) or 0) + tx["values"][key]
    return dict(values)